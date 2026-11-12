#!/usr/bin/env python3
"""Save a Claude Code, Codex, or DeepSeek Harness session transcript as Markdown.

The converter preserves conversation text, tool calls, and tool results in
order. It leaves out the model's reasoning blocks, subagent conversations and
context injected by the host, and redacts attached documents, e-mail
addresses, and strings that look like tokens or private keys with inline
notes. Check the output before sharing it.

Usage:
    export_log.py [--host auto|claude|codex|dsh] [--session ID] [--slug NAME]
                  [--out-dir DIR] [--project-dir DIR] [--transcript FILE]

Transcript stores:
    claude  ~/.claude/projects/<encoded project path>/<session>.jsonl
    codex   $CODEX_HOME/sessions/YYYY/MM/DD/rollout-<time>-<session>.jsonl
            (CODEX_HOME defaults to ~/.codex)
    dsh     $DSH_HOME/sessions/<encoded project path>/<session>/
            session[.vN].jsonl[.zstd] (DSH_HOME defaults to ~/.dsh)

With --host auto the host is taken from the environment (CLAUDECODE for
Claude Code, CODEX_THREAD_ID for Codex, DSH_SESSION_ID for DeepSeek Harness),
then from --transcript, then from whichever store holds the newest transcript
for the project. Without --session, CODEX_THREAD_ID is used for Codex and
DSH_SESSION_ID for DeepSeek Harness when they are set.

If a log for the same session already exists in the output directory (same
"Started" timestamp), it is refreshed in place. Otherwise a new file
NN-<slug>.md is created with the next free number.

Prints a one-line JSON summary. Exit codes: 0 ok, 2 usage error or no
transcript.
"""

import argparse
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DOCUMENT_NOTE = "[REDACTED: attached document]"
EMAIL_NOTE = "[REDACTED: e-mail address]"
SECRET_NOTE = "[REDACTED: secret-like string]"
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
# Addresses that are not personal data and must stay readable.
KEEP_EMAILS = {"noreply@anthropic.com", "git@github.com"}
SECRET_RE = re.compile(
    r"gh[pousr]_[A-Za-z0-9]{20,}"
    r"|github_pat_[A-Za-z0-9_]{20,}"
    r"|\bsk-[A-Za-z0-9_-]{20,}"
    r"|AKIA[0-9A-Z]{16}"
    r"|Bearer [A-Za-z0-9._-]{20,}"
    r"|BEGIN [A-Z ]*PRIVATE KEY"
)
HOST_NAMES = {"claude": "Claude Code", "codex": "Codex", "dsh": "DeepSeek Harness"}
ASSISTANT_NAMES = {"claude": "Claude", "codex": "Codex", "dsh": "DeepSeek"}
CLAUDE_ENTRYPOINTS = {"claude-desktop": "desktop app", "cli": "CLI"}
# Codex threads that are not the user's own conversation.
CODEX_SKIP_THREADS = {"subagent", "guardian_review"}
# Prefixes of user-role messages that Codex injects as context.
CODEX_INJECTED = ("<", "# AGENTS.md instructions", "# Files mentioned by the user")
CODEX_SCAN_LIMIT = 500
# Session-log generations found beside each DSH session: session.jsonl for
# version 0, session.vN.jsonl afterwards, with .zstd when compression is on.
DSH_GENERATION_RE = re.compile(r"^session(?:\.v([0-9]+))?\.jsonl(\.zstd)?$")
DSH_SCAN_LIMIT = 500

try:  # Python 3.14+ ships zstd decompression in the standard library.
    from compression.zstd import decompress as _zstd_frame_decompress
    from compression.zstd import get_frame_size as _zstd_frame_size
except ImportError:  # pragma: no cover - depends on the interpreter
    _zstd_frame_decompress = None
    _zstd_frame_size = None

counts = {"document": 0, "email": 0, "secret": 0, "thinking": 0}


def fail(message: str):
    print(message, file=sys.stderr)
    sys.exit(2)


# --- zstd transcript decoding ----------------------------------------------
#
# DSH appends one zstd frame per write batch, so a live session log is a
# sequence of frames and its tail can be a frame still being written. Decode
# every complete frame and keep the recovered prefix instead of failing on
# that tail.


def _zstd_stdlib(data: bytes):
    if _zstd_frame_decompress is None:
        return None
    out, pos = [], 0
    while pos < len(data):
        try:
            size = _zstd_frame_size(data[pos:])
        except Exception:
            break
        if not size or pos + size > len(data):
            break
        try:
            out.append(_zstd_frame_decompress(data[pos:pos + size]))
        except Exception:
            break
        pos += size
    return b"".join(out) if out else None


def _zstd_module(data: bytes):
    try:
        import zstandard
    except ImportError:
        return None
    out = bytearray()
    reader = None
    try:
        try:
            reader = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data), read_across_frames=True)
        except TypeError:
            reader = zstandard.ZstdDecompressor().stream_reader(io.BytesIO(data))
        while True:
            try:
                chunk = reader.read(1 << 20)
            except Exception:
                break
            if not chunk:
                break
            out += chunk
    except Exception:
        return None
    finally:
        if reader is not None:
            try:
                reader.close()
            except Exception:
                pass
    return bytes(out) if out else None


def _zstd_cli(data: bytes):
    for argv in (("zstd", "-dc"), ("unzstd", "-c")):
        try:
            proc = subprocess.run(argv, input=data, capture_output=True)
        except (OSError, ValueError):
            continue
        if proc.stdout:
            return proc.stdout
    return None


def decode_zstd_frames(data: bytes) -> bytes:
    """Return every complete frame decoded, tolerating an unfinished tail."""
    for decoder in (_zstd_stdlib, _zstd_module, _zstd_cli):
        out = decoder(data)
        if out is not None:
            return out
    return b""


def decompress_zstd(data: bytes) -> bytes:
    out = decode_zstd_frames(data)
    if not out:
        fail(
            "cannot read a .zstd transcript: install Python 3.14+, the zstandard "
            "module (pip install zstandard), or the zstd CLI"
        )
    return out


def read_log_text(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix == ".zstd":
        data = decompress_zstd(data)
    return data.decode("utf-8", "replace")


def scrub(text: str) -> str:
    def secret(match):
        counts["secret"] += 1
        return SECRET_NOTE

    def email(match):
        if match.group(0) in KEEP_EMAILS:
            return match.group(0)
        counts["email"] += 1
        return EMAIL_NOTE

    return EMAIL_RE.sub(email, SECRET_RE.sub(secret, text))


def fence(text: str, lang: str = "") -> str:
    longest = max((len(run) for run in re.findall(r"`+", text)), default=0)
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{lang}\n{text}\n{ticks}"


def blocks_text(content) -> str:
    """Flatten a content value of either host into plain text."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        content = [content]
    parts = []
    for block in content:
        kind = block.get("type")
        if kind in ("text", "input_text", "output_text"):
            parts.append(block.get("text", ""))
        elif kind in ("document", "file"):
            counts["document"] += 1
            parts.append(DOCUMENT_NOTE)
        elif kind == "tool_reference":
            parts.append(f"[tool reference: {block.get('tool_name', '')}]")
        elif kind in ("image", "input_image", "local_image"):
            parts.append("[image omitted]")
        else:
            parts.append(f"[{kind} block omitted]")
    return "\n".join(parts)


def read_jsonl(path: Path):
    if path.suffix != ".zstd":
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield json.loads(line)
        return
    for line in read_log_text(path).splitlines():
        line = line.strip()
        if line:
            yield json.loads(line)


def first_record(path: Path) -> dict:
    try:
        if path.suffix != ".zstd":
            with path.open(encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        return json.loads(line)
            return {}
        # The header sits in the first frame. Decode a bounded prefix first and
        # fall back to the whole log if that frame is larger than the prefix.
        with path.open("rb") as fh:
            head = fh.read(1 << 20)
        text = decode_zstd_frames(head).decode("utf-8", "replace") if head else ""
        if not text.strip():
            text = read_log_text(path)
        first = text.splitlines()[0].strip() if text else ""
        return json.loads(first) if first else {}
    except (OSError, ValueError):
        return {}


# --- transcript lookup -----------------------------------------------------


def claude_store(project_dir: Path) -> Path:
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(project_dir))


def codex_store() -> Path:
    return Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex") / "sessions"


def dsh_store() -> Path:
    home = (os.environ.get("DSH_HOME") or "").strip()
    return (Path(home).expanduser() if home else Path.home() / ".dsh") / "sessions"


def utf16_units(text: str):
    """Yield the UTF-16 code units of text, matching the host's JS path codec."""
    data = text.encode("utf-16-le")
    for index in range(0, len(data), 2):
        yield data[index] | (data[index + 1] << 8)


def dsh_encode_segment(raw: str) -> str:
    """Encode one DSH path segment: safe characters stay, others become ~XXXX."""
    if raw == "":
        raise ValueError("cannot encode an empty path segment")
    if raw == ".":
        return "~002E"
    if raw == "..":
        return "~002E~002E"
    out = []
    for code in utf16_units(raw):
        ch = chr(code)
        out.append(ch if ch != "~" and re.fullmatch(r"[A-Za-z0-9._-]", ch) else f"~{code:04X}")
    return "".join(out)


def dsh_project_key(cwd: str) -> str:
    """Readable DSH project directory name for a session's working directory."""
    if cwd == "":
        raise ValueError("cannot encode an empty project path")
    out, separator_run = [], False
    for code in utf16_units(cwd):
        ch = chr(code)
        if ch in ("/", "\\", ":"):
            if not separator_run:
                out.append("-")
            separator_run = True
        elif ch != "~" and re.fullmatch(r"[A-Za-z0-9._-]", ch):
            out.append(ch)
            separator_run = False
        else:
            out.append(f"~{code:04X}")
            separator_run = False
    readable = re.sub(r"^-+", "", "".join(out)) or "root"
    return f"--{readable[:251]}--"


def dsh_session_logs(session_dir: Path) -> list:
    """Existing generation logs in one session directory, oldest generation first."""
    logs = []
    try:
        entries = list(session_dir.iterdir())
    except OSError:
        return logs
    for path in entries:
        match = DSH_GENERATION_RE.match(path.name)
        if match and path.is_file():
            try:
                logs.append((int(match.group(1) or 0), path.stat().st_mtime, path))
            except OSError:
                continue
    return sorted(logs)


def dsh_best_log(session_dir: Path):
    logs = dsh_session_logs(session_dir)
    return logs[-1][2] if logs else None


def dsh_has_conversation(path: Path) -> bool:
    """True once the log holds a real user message or a visible assistant reply."""
    for record in read_jsonl(path):
        kind = record.get("type")
        if kind not in ("user/message", "assistant/message") or record.get("surfaceOp") != "append":
            continue
        data = record.get("data") or {}
        if kind == "user/message":
            if (data.get("source") or {}).get("kind") != "user":
                continue
            text = "\n".join(
                block.get("text", "") for block in data.get("content") or [] if block.get("type") == "text"
            )
        else:
            blocks = (data.get("message") or {}).get("content") or []
            text = "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text")
        if text.strip():
            return True
    return False


def find_dsh(project_dir: Path, session: str):
    store = dsh_store()
    if not store.is_dir():
        return None, True
    if session:
        segment = dsh_encode_segment(session)
        candidates = []
        keyed = store / dsh_project_key(str(project_dir)) / segment
        if keyed.is_dir():
            candidates.append(keyed)
        for path in store.glob(f"*/{segment}"):
            if path.is_dir() and path not in candidates:
                candidates.append(path)
        for session_dir in candidates:
            log = dsh_best_log(session_dir)
            if log is not None:
                return log, False
    # Sessions are grouped by project directory, but cwd spellings can differ
    # (symlinks), so confirm the fallback against the header's cwd and skip
    # subagent and teammate sessions. The transcript being written now is the
    # newest one.
    transcripts = []
    try:
        session_dirs = list(store.glob("*/*"))
    except OSError:
        session_dirs = []
    for session_dir in session_dirs:
        if not session_dir.is_dir():
            continue
        log = dsh_best_log(session_dir)
        if log is not None:
            try:
                transcripts.append((log.stat().st_mtime, log))
            except OSError:
                continue
    transcripts.sort(reverse=True)
    for _, path in transcripts[:DSH_SCAN_LIMIT]:
        header = first_record(path)
        if header.get("type") != "session":
            continue
        if header.get("parentSession") or header.get("origin") == "subagent":
            continue
        cwd = header.get("cwd")
        if not cwd:
            continue
        try:
            matches = Path(cwd).resolve() == project_dir
        except OSError:
            matches = False
        if matches and dsh_has_conversation(path):
            return path, True
    return None, True


def find_claude(project_dir: Path, session: str):
    store = claude_store(project_dir)
    if session:
        candidate = store / f"{session}.jsonl"
        if candidate.is_file():
            return candidate, False
    # The desktop app can resume a conversation under a new session id, so the
    # id we were given may not have a file. The transcript being written right
    # now is the newest one.
    transcripts = sorted(store.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return (transcripts[-1], True) if transcripts else (None, True)


def codex_meta_matches(path: Path, project_dir: Path) -> bool:
    record = first_record(path)
    if record.get("type") != "session_meta":
        return False
    meta = record.get("payload") or {}
    if meta.get("thread_source") in CODEX_SKIP_THREADS:
        return False
    cwd = meta.get("cwd")
    return bool(cwd) and Path(cwd).resolve() == project_dir


def find_codex(project_dir: Path, session: str):
    store = codex_store()
    if not store.is_dir():
        return None, True
    if session:
        matches = sorted(store.rglob(f"rollout-*-{session}.jsonl"))
        if matches:
            return matches[-1], False
    transcripts = sorted(store.rglob("rollout-*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    for path in transcripts[:CODEX_SCAN_LIMIT]:
        if codex_meta_matches(path, project_dir):
            return path, True
    return None, True


def detect_host(args, project_dir: Path) -> str:
    if args.host != "auto":
        return args.host
    if args.transcript:
        record = first_record(Path(args.transcript))
        if record.get("type") == "session_meta":
            return "codex"
        if record.get("type") == "session" and "version" in record:
            return "dsh"
        return "claude"
    if os.environ.get("CLAUDECODE"):
        return "claude"
    if os.environ.get("CODEX_THREAD_ID"):
        return "codex"
    if os.environ.get("DSH_SESSION_ID"):
        return "dsh"
    found = []
    for host, finder in (("claude", find_claude), ("codex", find_codex), ("dsh", find_dsh)):
        path, _ = finder(project_dir, args.session)
        if path:
            found.append((path.stat().st_mtime, host))
    if not found:
        fail(f"no Claude Code, Codex, or DeepSeek Harness transcripts found for {project_dir}")
    return max(found)[1]


def find_transcript(args, host: str, project_dir: Path):
    """Return (path, fell_back_to_newest)."""
    if args.transcript:
        return Path(args.transcript), False
    session = args.session
    if host == "codex" and not session:
        session = os.environ.get("CODEX_THREAD_ID", "")
    if host == "dsh" and not session:
        session = os.environ.get("DSH_SESSION_ID", "")
    finder = {"codex": find_codex, "dsh": find_dsh}.get(host, find_claude)
    path, fallback = finder(project_dir, session)
    if path is None:
        if host == "codex":
            where = codex_store()
        elif host == "dsh":
            where = dsh_store()
        else:
            where = claude_store(project_dir)
        fail(f"no {HOST_NAMES[host]} transcripts for {project_dir} in {where}")
    return path, fallback


# --- parsing into a common event list --------------------------------------
#
# Events: ("user", ts, text) | ("text", ts, text)
#         | ("call", ts, name, payload, lang, call_id)
# plus a dict of call_id -> result text.


def parse_claude(path: Path) -> dict:
    rows = [
        r for r in read_jsonl(path)
        if r.get("type") in ("user", "assistant") and not r.get("isSidechain")
    ]
    results, events = {}, []
    for row in rows:
        content = row["message"].get("content")
        if row["type"] == "user" and isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_result":
                    results[block["tool_use_id"]] = blocks_text(block.get("content"))

    for row in rows:
        ts = row.get("timestamp", "")
        content = row["message"].get("content")
        if row["type"] == "user":
            if isinstance(content, str):
                text = content
            else:
                user_blocks = [b for b in (content or []) if b.get("type") != "tool_result"]
                text = blocks_text(user_blocks) if user_blocks else ""
            if text:
                events.append(("user", ts, text))
            continue
        for block in content or []:
            kind = block.get("type")
            if kind in ("thinking", "redacted_thinking"):
                counts["thinking"] += 1
            elif kind == "text":
                events.append(("text", ts, block.get("text", "")))
            elif kind == "tool_use":
                call = json.dumps(block.get("input", {}), indent=2, ensure_ascii=False)
                events.append(("call", ts, block.get("name"), call, "json", block.get("id")))

    model = next(
        (r["message"].get("model") for r in rows if r["type"] == "assistant" and r["message"].get("model")),
        "unknown",
    )
    entrypoint = next((r.get("entrypoint") for r in rows if r.get("entrypoint")), "")
    return {
        "events": events,
        "results": results,
        "messages": len(rows),
        "model": model,
        "started": next((r.get("timestamp") for r in rows if r.get("timestamp")), "unknown"),
        "surface": CLAUDE_ENTRYPOINTS.get(entrypoint, entrypoint or "unknown surface"),
    }


def codex_call(payload: dict):
    """Return (name, text, lang) for a Codex *_call response item."""
    kind = payload.get("type")
    name = payload.get("name") or kind
    if payload.get("namespace") and payload.get("namespace") not in ("functions",):
        name = f"{payload['namespace']}.{name}"
    if kind == "custom_tool_call":
        return name, str(payload.get("input", "")), ""
    if kind == "function_call":
        raw = payload.get("arguments", "")
        try:
            return name, json.dumps(json.loads(raw), indent=2, ensure_ascii=False), "json"
        except (TypeError, ValueError):
            return name, str(raw), ""
    body = payload.get("action", payload.get("input", payload.get("arguments", {})))
    return name, json.dumps(body, indent=2, ensure_ascii=False), "json"


def parse_codex(path: Path) -> dict:
    records = list(read_jsonl(path))
    meta = next((r.get("payload") or {} for r in records if r.get("type") == "session_meta"), {})
    model = next(
        ((r.get("payload") or {}).get("model") for r in records
         if r.get("type") == "turn_context" and (r.get("payload") or {}).get("model")),
        "unknown",
    )
    # Newer Codex versions log the user's own text as UserMessage items; the
    # user-role response items also carry injected context (AGENTS.md,
    # environment, plugins). Fall back to those only when no items exist.
    use_items = any(
        r.get("type") == "event_msg"
        and (r.get("payload") or {}).get("type") == "item_completed"
        and ((r.get("payload") or {}).get("item") or {}).get("type") == "UserMessage"
        for r in records
    )

    results, events, messages = {}, [], 0
    for record in records:
        ts = record.get("timestamp", "")
        payload = record.get("payload") or {}
        kind = payload.get("type") if isinstance(payload, dict) else None
        if record.get("type") == "event_msg":
            item = payload.get("item") or {}
            if use_items and kind == "item_completed" and item.get("type") == "UserMessage":
                text = blocks_text(item.get("content"))
                if text.strip():
                    events.append(("user", ts, text))
                    messages += 1
            continue
        if record.get("type") != "response_item":
            continue
        if kind == "reasoning":
            counts["thinking"] += 1
        elif kind == "message" and payload.get("role") == "assistant":
            text = blocks_text(payload.get("content"))
            if text.strip():
                events.append(("text", ts, text))
                messages += 1
        elif kind == "message" and payload.get("role") == "user" and not use_items:
            kept = [
                b for b in payload.get("content") or []
                if not b.get("text", "").lstrip().startswith(CODEX_INJECTED)
            ]
            text = blocks_text(kept)
            if text.strip():
                events.append(("user", ts, text))
                messages += 1
        elif kind == "compaction":
            events.append(("text", ts, "_[context compacted]_"))
        elif kind and kind.endswith("_call_output"):
            results[payload.get("call_id")] = blocks_text(payload.get("output"))
        elif kind and kind.endswith("_call"):
            name, text, lang = codex_call(payload)
            events.append(("call", ts, name, text, lang, payload.get("call_id")))
            messages += 1

    return {
        "events": events,
        "results": results,
        "messages": messages,
        "model": model,
        "started": meta.get("timestamp") or (records[0].get("timestamp") if records else "unknown"),
        "surface": meta.get("originator") or "unknown surface",
    }


def dsh_time(milliseconds) -> str:
    """Format a DSH epoch-millisecond timestamp as UTC ISO 8601."""
    if not isinstance(milliseconds, (int, float)):
        return ""
    moment = datetime.fromtimestamp(milliseconds / 1000, timezone.utc)
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def dsh_visible(content, *, user: bool) -> str:
    """Visible text of DSH content blocks; attachments become redaction notes."""
    parts = []
    for block in content or []:
        kind = block.get("type")
        if kind == "text":
            if block.get("text"):
                parts.append(block.get("text"))
        elif kind == "file":
            counts["document"] += 1
            parts.append(DOCUMENT_NOTE)
        elif kind == "image" and user:
            parts.append("[image omitted]")
    return "\n".join(parts)


def parse_dsh(path: Path) -> dict:
    """Parse a DSH session log.

    Only append-origin events are conversation history: replacement copies are
    model-only shadowing, so keeping appends preserves what the user saw even
    after compaction. Reasoning, system and developer messages, injected
    runtime context, request records, and subagent/teammate traffic are omitted.
    """
    records = list(read_jsonl(path))
    header = next((r for r in records if r.get("type") == "session"), {})
    results, events, messages, model = {}, [], 0, ""
    for record in records:
        kind = record.get("type")
        data = record.get("data") or {}
        ts = dsh_time(record.get("time"))
        if kind == "request/header" and not model:
            model = ((data.get("header") or {}).get("config") or {}).get("model") or ""
        if kind in ("user/message", "assistant/message", "tool/result") and record.get("surfaceOp") != "append":
            continue
        if kind == "user/message":
            if (data.get("source") or {}).get("kind") != "user":
                continue
            text = dsh_visible(data.get("content"), user=True)
            if text.strip():
                events.append(("user", ts, text))
                messages += 1
        elif kind == "assistant/message":
            message = data.get("message") or {}
            blocks = message.get("content") or []
            counts["thinking"] += sum(1 for block in blocks if block.get("type") == "reasoning")
            text = dsh_visible([block for block in blocks if block.get("type") == "text"], user=False)
            if text.strip():
                events.append(("text", ts, text))
                messages += 1
            source = message.get("source") or {}
            if not model and source.get("kind") == "model" and source.get("model"):
                model = source.get("model")
        elif kind == "tool/call":
            name = data.get("name") or "unknown"
            raw = data.get("arguments") or ""
            try:
                payload, lang = json.dumps(json.loads(raw), indent=2, ensure_ascii=False), "json"
            except (TypeError, ValueError):
                payload, lang = str(raw), ""
            events.append(("call", ts, name, payload, lang, data.get("callId")))
            messages += 1
        elif kind == "tool/result":
            message = data.get("message") or {}
            text = dsh_visible(message.get("content"), user=False)
            reason = (data.get("error") or {}).get("reason")
            if reason:
                text = f"Error: {reason}" + (f"\n\n{text}" if text else "")
            results[message.get("toolCallId")] = text

    started = dsh_time(header.get("createdAt")) or next((event[1] for event in events if event[1]), "unknown")
    profile = os.environ.get("DSH_PROFILE", "")
    return {
        "events": events,
        "results": results,
        "messages": messages,
        "model": model or "unknown",
        "started": started,
        "surface": f"{profile} profile" if profile else "unknown surface",
    }


def render_body(parsed: dict, assistant: str) -> list:
    body = []
    in_assistant = False
    for event in parsed["events"]:
        kind, ts = event[0], event[1]
        if kind == "user":
            body.append(f"## 🧑 User · {ts}\n\n{scrub(event[2])}\n")
            in_assistant = False
            continue
        if not in_assistant:
            body.append(f"## 🤖 {assistant} · {ts}\n")
            in_assistant = True
        if kind == "text":
            body.append(f"{scrub(event[2])}\n")
        else:
            _, _, name, payload, lang, call_id = event
            body.append(f"**🔧 Tool call: `{name}`**\n\n{fence(scrub(payload), lang)}\n")
            if call_id in parsed["results"]:
                out = scrub(parsed["results"][call_id])
                body.append(f"<details><summary>Tool result</summary>\n\n{fence(out)}\n\n</details>\n")
    return body


def choose_target(out_dir: Path, started: str, slug: str):
    """Return (path, created). Reuse the log of the same session if there is one."""
    marker = f"- Started: {started}"
    highest = -1
    for path in sorted(out_dir.glob("*.md")):
        match = re.match(r"(\d+)-", path.name)
        if match:
            highest = max(highest, int(match.group(1)))
        with path.open(encoding="utf-8") as fh:
            head = [next(fh, "") for _ in range(8)]
        if any(line.strip() == marker for line in head):
            return path, False
    if not slug:
        fail("this session has no log yet: pass --slug, for example --slug implementation-session")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", slug):
        fail("--slug must be lower-case words joined by hyphens")
    return out_dir / f"{highest + 1:02d}-{slug}.md", True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--host", choices=("auto", "claude", "codex", "dsh"), default="auto")
    parser.add_argument("--session", default="", help="session id; falls back to the newest transcript")
    parser.add_argument("--slug", default="", help="name for a new log, e.g. implementation-session")
    parser.add_argument("--out-dir", default="docs/ai-logs", help="relative paths resolve against --project-dir")
    parser.add_argument("--project-dir", default=".", help="project root the session ran in")
    parser.add_argument("--transcript", default="", help="explicit path to a .jsonl transcript")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    host = detect_host(args, project_dir)
    transcript, fallback = find_transcript(args, host, project_dir)
    if not transcript.is_file():
        fail(f"transcript not found: {transcript}")
    parsed = {"codex": parse_codex, "dsh": parse_dsh}.get(host, parse_claude)(transcript)
    if not parsed["events"]:
        fail(f"no conversation in {transcript}")

    # A relative --out-dir is resolved against the project root, not the shell's
    # current directory, so the log lands in the right repository.
    out_dir = Path(args.out_dir).expanduser()
    if not out_dir.is_absolute():
        out_dir = project_dir / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    target, created = choose_target(out_dir, parsed["started"], args.slug)

    body = render_body(parsed, ASSISTANT_NAMES[host])

    redactions = []
    if counts["document"]:
        redactions.append(f"attached documents ({counts['document']}×)")
    if counts["email"]:
        redactions.append(f"e-mail addresses ({counts['email']}×)")
    if counts["secret"]:
        redactions.append(f"secret-like strings ({counts['secret']}×)")
    if len(redactions) > 1:
        redactions[-1] = "and " + redactions[-1]
    joiner = ", " if len(redactions) > 2 else " "
    redaction_note = " Redactions, noted inline: " + joiner.join(redactions) + "." if redactions else ""

    tool = HOST_NAMES[host]
    header = (
        f"# {tool} session: {target.stem}\n\n"
        f"- Tool: {tool} ({parsed['surface']}), model `{parsed['model']}`\n"
        f"- Started: {parsed['started']}\n"
        "- Export: transcript converted to Markdown by script without manual edits. "
        "The model's reasoning blocks are left out."
        f"{redaction_note}\n"
        "- The export was run during the session's last turn, so the log ends partway through that turn.\n\n"
        "---\n\n"
    )
    target.write_text(header + "\n".join(body), encoding="utf-8")

    summary = {
        "file": str(target),
        "action": "created" if created else "refreshed",
        "host": host,
        "transcript": transcript.name,
        "fell_back_to_newest": fallback,
        "started": parsed["started"],
        "model": parsed["model"],
        "messages": parsed["messages"],
        "reasoning_blocks_left_out": counts["thinking"],
        "redacted_documents": counts["document"],
        "redacted_emails": counts["email"],
        "redacted_secrets": counts["secret"],
    }
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())

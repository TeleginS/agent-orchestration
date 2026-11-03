#!/usr/bin/env python3
"""PreToolUse(Read/Edit/Write/Grep/Bash/apply_patch): protect configured secret files.

A secret name is a basename or fnmatch pattern from `secret_names`; `<name>.<suffix>`
variants (`.env.local`) match too, and matching ignores case because the usual macOS file
system does. A matching directory name protects its children. Names in `secret_allow`
(`.env.example`) stay readable unless a parent directory is protected. In Bash, the grep
pattern argument and metadata-only git pathspecs after `--` are not treated as files; `ls`, `stat`, `test`
and `git check-ignore` do not read contents. Shell globs (`.env*`, `*.p8`), brace expansions
(`.{env,}`), redirections (`0<.env`) and `<rev>:<path>` forms are resolved before matching.
"""
import fnmatch
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from lib import block, expand_braces, read_payload, segments  # noqa: E402

MSG = (
    "Blocked by secrets-gate: %s is closed to agents. The owner sets secrets locally; "
    "use the committed example file to learn the structure."
)
# Commands that do not read file contents
NON_READING = {"ls", "stat", "test", "[", "[["}
GREP_LIKE = {"grep", "egrep", "fgrep", "rg", "ag"}
GREP_VALUE_FLAGS = {"-e", "-f", "-m", "-A", "-B", "-C", "--regexp", "--file", "--max-count",
                    "--include", "--exclude", "--exclude-dir", "-g", "--glob", "--iglob", "-t", "--type"}
# Values of these flags select files to read, so they are checked like file arguments
GREP_FILE_FLAGS = {"-f", "--file", "--include", "-g", "--glob", "--iglob"}
METADATA_GIT = {"status", "ls-files", "check-ignore"}
GLOB_CHARS = "*?["
_REDIRECT = re.compile(r"^\d*[<>&|]+")


class Secrets:
    def __init__(self, cfg):
        self.names = [n.lower() for n in cfg["secret_names"]]
        self.allow = {a.lower() for a in cfg["secret_allow"]}
        self.literals = [n for n in self.names if not any(c in n for c in GLOB_CHARS)]

    def is_secret_name(self, name):
        name = name.lower()
        if not name or name in self.allow:
            return False
        return any(fnmatch.fnmatchcase(name, n) or name.startswith(n + ".") for n in self.names)

    def is_secret_path(self, path):
        components = [p for p in path.replace("\\", "/").split("/") if p and p != "."]
        if not components:
            return False
        # A leaf allowlist entry cannot reopen a protected parent directory.
        return any(self.is_secret_name(p) for p in components[:-1]) or self.is_secret_name(components[-1])

    def matches_glob(self, name):
        """A shell glob in the command (`.env*`, `*.p8`, `[S]ecrets.xcconfig`) that expands to a secret.

        The pattern needs a literal letter or digit: a bare `*` would block every `grep foo *`.
        Like the shell, a leading wildcard does not match a leading dot.
        """
        name = name.lower()
        if not any(c in name for c in GLOB_CHARS) or not re.search(r"[a-z0-9]", re.sub(r"\[[^\]]*\]", "", name)):
            return False
        return any(fnmatch.fnmatchcase(s, name) for s in self.literals
                   if not (s.startswith(".") and name[0] in GLOB_CHARS))

    def token_hits(self, tok):
        for word in expand_braces(tok):
            parts = {word, word.split("=", 1)[-1], _REDIRECT.sub("", word), word.rsplit(":", 1)[-1]}
            for part in parts:
                name = os.path.basename(part.rstrip("/"))
                if self.is_secret_path(part) or self.matches_glob(name):
                    return True
        return False


def short_cluster_value(a):
    """For `-efoo`, `-rnefoo`, `-rne`, `-g.env`: (flag letter e/f/g, attached value) or None."""
    if len(a) < 2 or a[0] != "-" or a[1] == "-":
        return None
    for i, ch in enumerate(a[1:], 1):
        if ch in "efg":
            return ch, a[i + 1:]
    return None


def tokens_to_check(seg):
    """Tokens of a segment that the command may open as a file.

    The grep PATTERN and metadata-only git pathspecs after `--` do not read file contents.
    """
    head = os.path.basename(seg[0])
    if head in GREP_LIKE:
        args = seg[1:]
        explicit = any(a in {"-e", "--regexp", "-f", "--file"} or a.startswith(("--regexp=", "--file="))
                       or (short_cluster_value(a) or ("",))[0] in {"e", "f"} for a in args)
        skip_pattern = not explicit
        out, flag = [], None
        for a in args:
            if flag:
                if flag in GREP_FILE_FLAGS:  # a pattern file or an include glob is read
                    out.append(a)
                flag = None
            elif a.startswith("-") and a != "-":
                cluster = short_cluster_value(a)
                if cluster and a not in GREP_VALUE_FLAGS:
                    letter, attached = cluster
                    if attached:  # -efoo / -ffile / -g.env: the value is attached
                        if letter in "fg":
                            out.append(attached)
                    else:  # -rne: the value is the next argument
                        flag = "-" + letter
                elif a in GREP_VALUE_FLAGS:
                    flag = a
                else:
                    out.append(a)
            elif skip_pattern:
                skip_pattern = False
            else:
                out.append(a)
        return out
    if head == "git":
        words = [a for a in seg[1:] if not a.startswith("-")]
        if words and words[0] in METADATA_GIT and "--" in seg:
            return seg[:seg.index("--")]
    return seg


def patch_paths(patch):
    """Inspect patch headers only; added/context lines are file content, not paths."""
    if not isinstance(patch, str):
        block("Blocked by secrets-gate: apply_patch input has no string command; cannot check paths.")
    prefixes = ("*** Add File: ", "*** Update File: ", "*** Delete File: ", "*** Move to: ")
    for line in patch.splitlines():
        for prefix in prefixes:
            if line.startswith(prefix):
                yield line[len(prefix):].strip()
                break


def main():
    payload = read_payload()
    tool = payload.get("tool_name", "")
    tin = payload.get("tool_input") or {}
    secrets = Secrets(config.get())
    if tool == "Bash":
        for seg in segments(tin.get("command") or ""):
            head = os.path.basename(seg[0])
            for i, tok in enumerate(seg):
                if _REDIRECT.match(tok) and (tok.lstrip("0123456789")[:1] in "<>"):
                    target = _REDIRECT.sub("", tok) or (seg[i + 1] if i + 1 < len(seg) else "")
                    if secrets.token_hits(target):
                        block(MSG % target)
            if head in NON_READING or seg[:2] == ["git", "check-ignore"]:
                continue
            for tok in tokens_to_check(seg):
                if secrets.token_hits(tok):
                    block(MSG % tok)
    elif tool == "apply_patch":
        for path in patch_paths(tin.get("command")):
            # Accept either separator so a Windows payload is checked on POSIX too.
            if secrets.is_secret_path(path):
                block(MSG % path)
    else:
        # Read/Edit/Write/MultiEdit use file_path, NotebookEdit notebook_path, Grep path (+ glob)
        path = tin.get("file_path") or tin.get("notebook_path") or tin.get("path") or ""
        if path and secrets.is_secret_path(path):
            block(MSG % path)
        pattern = tin.get("glob") or ""
        if pattern and secrets.token_hits(pattern):
            block(MSG % pattern)
    sys.exit(0)


if __name__ == "__main__":
    main()

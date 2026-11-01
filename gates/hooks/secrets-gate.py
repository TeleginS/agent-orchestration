#!/usr/bin/env python3
"""PreToolUse(Read/Edit/Write/Bash/apply_patch): protect configured secret files.

A secret name is a basename or fnmatch pattern from `secret_names`; `<name>.<suffix>`
variants (`.env.local`) match too. Names in `secret_allow` (`.env.example`) stay
readable. In Bash, the grep pattern argument and git pathspecs after `--` are not
treated as files; `ls`, `stat`, `test` and `git check-ignore` do not read contents.
"""
import fnmatch
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from lib import block, read_payload, segments  # noqa: E402

MSG = (
    "Blocked by secrets-gate: %s is closed to agents. The owner sets secrets locally; "
    "use the committed example file to learn the structure."
)
# Commands that do not read file contents
NON_READING = {"ls", "stat", "test", "[", "[["}
GREP_LIKE = {"grep", "egrep", "fgrep", "rg", "ag"}
GREP_VALUE_FLAGS = {"-e", "-f", "-m", "-A", "-B", "-C", "--regexp", "--file", "--max-count",
                    "--include", "--exclude", "--exclude-dir", "-g", "--glob", "-t", "--type"}
HISTORY_SUBCOMMANDS = {"log", "diff", "show", "shortlog", "whatchanged", "rev-list", "status", "ls-files"}
GLOB_CHARS = "*?["


class Secrets:
    def __init__(self, cfg):
        self.names = list(cfg["secret_names"])
        self.allow = set(cfg["secret_allow"])
        self.literals = [n for n in self.names if not any(c in n for c in GLOB_CHARS)]

    def is_secret_name(self, name):
        if not name or name in self.allow:
            return False
        return any(fnmatch.fnmatchcase(name, n) or name.startswith(n + ".") for n in self.names)

    def matches_glob(self, name):
        """A shell glob in the command (`.env*`) that would expand to a secret.

        Only globs with a literal prefix count: a bare `*` would block every `grep foo *`.
        """
        first = min((name.find(c) for c in GLOB_CHARS if c in name), default=-1)
        if first <= 0:
            return False
        prefix = name[:first]
        return any(s.startswith(prefix) and fnmatch.fnmatchcase(s, name) for s in self.literals)

    def token_hits(self, tok):
        for part in {tok, tok.split("=", 1)[-1], tok.lstrip("<>")}:
            name = os.path.basename(part.rstrip("/"))
            if self.is_secret_name(name) or self.matches_glob(name):
                return True
        return False


def short_cluster_value(a):
    """For `-efoo`, `-rnefoo`, `-rne`: (flag e/f, attached value) or None."""
    if len(a) < 2 or a[0] != "-" or a[1] == "-":
        return None
    for i, ch in enumerate(a[1:], 1):
        if ch in "ef":
            return ch, a[i + 1:]
    return None


def tokens_to_check(seg):
    """Tokens of a segment that the command may open as a file.

    The grep PATTERN and a git log/diff pathspec after `--` do not read the file.
    """
    head = os.path.basename(seg[0])
    if head in GREP_LIKE:
        args = seg[1:]
        explicit = any(a in {"-e", "--regexp", "-f", "--file"} or a.startswith(("--regexp=", "--file="))
                       or short_cluster_value(a) for a in args)
        skip_pattern = not explicit
        out, flag = [], None
        for a in args:
            if flag:
                if flag in {"-f", "--file"}:  # a pattern file is read
                    out.append(a)
                flag = None
            elif a.startswith("-") and a != "-":
                cluster = short_cluster_value(a)
                if cluster and a not in GREP_VALUE_FLAGS:
                    letter, attached = cluster
                    if attached:  # -efoo / -ffile: the value is attached
                        if letter == "f":
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
        if words and words[0] in HISTORY_SUBCOMMANDS and "--" in seg:
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
            if head in NON_READING or seg[:2] == ["git", "check-ignore"]:
                continue
            for tok in tokens_to_check(seg):
                if secrets.token_hits(tok):
                    block(MSG % tok)
    elif tool == "apply_patch":
        for path in patch_paths(tin.get("command")):
            # Accept either separator so a Windows payload is checked on POSIX too.
            name = path.replace("\\", "/").rsplit("/", 1)[-1]
            if secrets.is_secret_name(name):
                block(MSG % path)
    else:
        path = tin.get("file_path") or tin.get("notebook_path") or ""
        if path and secrets.is_secret_name(os.path.basename(path)):
            block(MSG % path)
    sys.exit(0)


if __name__ == "__main__":
    main()

"""Shared Bash-command parsing for the gate hooks: segments, wrappers (rtk, env, bash -c), tokens.

Hooks read the JSON tool input from stdin; exit 2 with a stderr message blocks the call.
Python 3 standard library only: no network, no build step.
"""
import json
import os
import re
import shlex
import sys

# Prefixes followed by the real command. `rtk` is added by a global RTK rewrite hook.
WRAPPERS = {"rtk", "sudo", "command", "env", "time", "nohup", "exec", "builtin", "nice", "xargs"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
OPERATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}", "\n"}


def read_payload():
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def block(message):
    print(message, file=sys.stderr)
    sys.exit(2)


_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2(?=\n|$)", re.S)


def _tokenize(command):
    # A heredoc body is data, not commands; a newline separates commands.
    command = _HEREDOC.sub(lambda m: m.group(0).split("\n", 1)[0], command)
    command = command.replace("`", " ; ").replace("\n", " ; ")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _split_segments(tokens):
    segments, current = [], []
    for tok in tokens:
        if tok and set(tok) <= set(";&|(){}") and tok in OPERATORS | {";;"}:
            if current:
                segments.append(current)
            current = []
        else:
            current.append(tok)
    if current:
        segments.append(current)
    return segments


def _strip_wrappers(seg):
    seg = list(seg)
    while seg:
        head = seg[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head):
            seg.pop(0)
        elif os.path.basename(head) in WRAPPERS:
            seg.pop(0)
            # wrapper options (env -i, sudo -u, rtk proxy) must not hide the command
            while seg and (seg[0].startswith("-") or seg[0] == "proxy"):
                seg.pop(0)
        else:
            break
    return seg


def segments(command, depth=0):
    """List of command segments; `bash -c "..."` and `eval` are expanded recursively."""
    try:
        raw = _split_segments(_tokenize(command))
    except ValueError:
        raw = [command.split()]
    result = []
    for seg in raw:
        seg = _strip_wrappers(seg)
        if not seg:
            continue
        result.append(seg)
        if depth < 4 and os.path.basename(seg[0]) in SHELLS:
            for i, tok in enumerate(seg[1:], 1):
                if tok.startswith("-") and "c" in tok[1:] and not tok.startswith("--") and i + 1 < len(seg):
                    result.extend(segments(seg[i + 1], depth + 1))
                    break
        if depth < 4 and os.path.basename(seg[0]) in {"eval"}:
            result.extend(segments(" ".join(seg[1:]), depth + 1))
    return result


def positional(args, value_flags=()):
    """Arguments that are not flags; values of flags listed in value_flags are skipped."""
    out, skip = [], False
    for a in args:
        if skip:
            skip = False
        elif a.startswith("-") and a != "-":
            skip = a in value_flags
        else:
            out.append(a)
    return out

"""Shared Bash-command parsing for the gate hooks: segments, wrappers (rtk, env, bash -c), tokens.

Hooks read the JSON tool input from stdin; exit 2 with a stderr message blocks the call.
Python 3 standard library only: no network, no build step.
"""
import json
import os
import re
import shlex
import sys

# Prefixes followed by the real command, each with the options that take a value, so that
# `sudo -u root git push` does not make `root` the command. `rtk` is added by a global RTK
# rewrite hook.
WRAPPERS = {
    "rtk": set(),
    "sudo": {"-u", "--user", "-g", "--group", "-C", "--close-from", "-D", "--chdir", "-h", "--host",
             "-p", "--prompt", "-r", "--role", "-t", "--type", "-T", "--command-timeout", "-U", "--other-user"},
    "doas": {"-u", "-C"},
    "command": set(),
    "builtin": set(),
    "exec": {"-a"},
    "env": {"-u", "--unset", "-C", "--chdir", "--default-signal", "--ignore-signal", "--block-signal"},
    "time": {"-f", "--format", "-o", "--output"},
    "nohup": set(),
    "setsid": set(),
    "nice": {"-n", "--adjustment"},
    "ionice": {"-c", "--class", "-n", "--classdata", "-p", "--pid", "-P", "--pgid", "-u", "--uid"},
    "timeout": {"-s", "--signal", "-k", "--kill-after"},
    "stdbuf": {"-i", "--input", "-o", "--output", "-e", "--error"},
    "caffeinate": {"-t", "-w"},
    "unbuffer": set(),
    "chronic": set(),
    "xargs": {"-I", "-n", "-L", "-P", "-s", "-E", "-d", "-a", "--replace", "--max-args", "--max-lines",
              "--max-procs", "--max-chars", "--eof", "--delimiter", "--arg-file", "--process-slot-var"},
    "flock": {"-w", "--wait", "--timeout", "-E", "--conflict-exit-code"},
}
# Wrappers whose first operand is not the command: a duration, a lock file.
LEADING_OPERANDS = {"timeout": 1, "flock": 1}
# The wrapped command receives extra arguments from stdin that the parser cannot see.
STDIN_WRAPPERS = {"xargs"}
SHELLS = {"bash", "sh", "zsh", "dash", "ksh"}
PRINTERS = {"echo", "printf"}
OPERATORS = {";", "&&", "||", "|", "&", "|&", "(", ")", "{", "}", "\n"}
CONTROL_PREFIXES = {"if", "elif", "then", "else", "while", "until", "do", "!"}
CONTROL_ENDS = {"fi", "done"}


class Segment(list):
    """One simple command. `stdin_args`: xargs feeds it arguments the parser cannot see.
    `nested`: command lines carried as a wrapper argument (`env -S "git push"`)."""
    stdin_args = False
    nested = ()


def read_payload():
    try:
        return json.load(sys.stdin)
    except (ValueError, OSError):
        return {}


def block(message):
    print(message, file=sys.stderr)
    sys.exit(2)


_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2(?=\n|$)", re.S)
# A shell brace expression (`.{env,}`) has no unquoted whitespace; `{}` alone is literal.
_BRACES = re.compile(r"\{[^{}\s]*,[^{}\s]*\}")
_ITEM, _LBRACE, _RBRACE = "\x03", "\x01", "\x02"


def _tokenize(command):
    # A heredoc body is data, not commands; a newline separates commands.
    command = _HEREDOC.sub(lambda m: m.group(0).split("\n", 1)[0], command)
    # `{}` (the xargs/find placeholder) and `{a,b}` are words, not command groups.
    command = command.replace("{}", _ITEM)
    command = _BRACES.sub(lambda m: m.group(0).replace("{", _LBRACE).replace("}", _RBRACE), command)
    command = command.replace("`", " ; ").replace("\n", " ; ")
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|(){}")
    lexer.whitespace_split = True
    lexer.commenters = ""
    return [t.replace(_ITEM, "{}").replace(_LBRACE, "{").replace(_RBRACE, "}") for t in lexer]


def _split_segments(tokens):
    """(segments, operators): operators[i] is the operator before segments[i], None for the first."""
    segments, operators, current, last_op = [], [], [], None
    for tok in tokens:
        if tok and set(tok) <= set(";&|(){}") and tok in OPERATORS | {";;"}:
            if current:
                segments.append(current)
                operators.append(last_op)
            current, last_op = [], tok
        else:
            current.append(tok)
    if current:
        segments.append(current)
        operators.append(last_op)
    return segments, operators


def _strip_wrappers(seg):
    seg, stdin_args, nested = Segment(seg), False, []
    while seg:
        head = seg[0]
        if re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", head):
            seg.pop(0)
            continue
        name = os.path.basename(head)
        if name not in WRAPPERS:
            break
        seg.pop(0)
        value_flags, operands = WRAPPERS[name], LEADING_OPERANDS.get(name, 0)
        stdin_args = stdin_args or name in STDIN_WRAPPERS
        # wrapper options (env -i, sudo -u root, rtk proxy) must not hide or become the command
        while seg:
            tok = seg[0]
            if name == "env" and (tok in {"-S", "--split-string"} or tok.startswith(("-S", "--split-string="))):
                seg.pop(0)  # `env -S "git push ..."`: the value is a command line
                if tok in {"-S", "--split-string"}:
                    nested.append(seg.pop(0) if seg else "")
                else:
                    nested.append(tok.split("=", 1)[1] if tok.startswith("--") else tok[2:])
            elif name == "rtk" and tok == "proxy":
                seg.pop(0)
            elif tok == "--":
                seg.pop(0)
                break
            elif tok.startswith("-") and tok != "-":
                seg.pop(0)
                if tok in value_flags and seg:
                    seg.pop(0)
            elif operands:
                operands -= 1
                seg.pop(0)
            else:
                break
    seg.stdin_args, seg.nested = stdin_args, nested
    return seg


def _shell_scripts(seg, prev, operator):
    """Command lines a shell segment runs: `-c "..."`, a here-string, or `echo "..." | sh`."""
    args, out, operands, i = seg[1:], [], [], 0
    while i < len(args):
        a = args[i]
        if a == "<<<" and i + 1 < len(args):
            out.append(args[i + 1])
            i += 2
        elif a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
            if i + 1 < len(args):
                out.append(args[i + 1])
            return out  # what follows the script is $0 and positional parameters
        elif a.startswith("-"):  # options, and `-` for "read the script from stdin"
            i += 1
        else:
            operands.append(a)
            i += 1
    if not out and not operands and operator == "|" and prev and os.path.basename(prev[0]) in PRINTERS:
        out.append(" ".join(prev[1:]))
    return out


def _heredoc_scripts(command):
    """Bodies of heredocs fed to a shell (`bash <<EOF`, `cat <<EOF | sh`): commands, not data."""
    for m in _HEREDOC.finditer(command):
        operator_line, body = m.group(0).split("\n", 1)
        first = command[command.rfind("\n", 0, m.start()) + 1:m.start()] + operator_line
        try:
            heads, _ = _split_segments(_tokenize(first))
        except ValueError:
            continue
        heads = [_strip_wrappers(h) for h in heads]
        if any(h and os.path.basename(h[0]) in SHELLS for h in heads):
            yield body.rsplit("\n", 1)[0]


def _launcher_scripts(seg):
    """Shell command strings executed by npx/npm exec -c or --call."""
    head = os.path.basename(seg[0]).split("@", 1)[0]
    if head != "npx" and not (head == "npm" and len(seg) > 1 and seg[1] == "exec"):
        return
    args = seg[1:]
    for i, arg in enumerate(args):
        if arg in {"-c", "--call"} and i + 1 < len(args):
            yield args[i + 1]
        elif arg.startswith("--call="):
            yield arg.partition("=")[2]
        elif arg.startswith("-c") and not arg.startswith("--") and len(arg) > 2:
            yield arg[2:]


def segments(command, depth=0):
    """List of command segments; `bash -c "..."`, `eval`, here-strings, `echo cmd | sh` and
    heredocs piped into a shell are expanded recursively."""
    try:
        raw, operators = _split_segments(_tokenize(command))
    except ValueError:
        raw, operators = [command.split()], [None]
    result = []
    for i, seg in enumerate(raw):
        # Shell control words occupy the command position. Their conditions and bodies
        # are still commands, including when a semicolon precedes then/do.
        while seg and seg[0] in CONTROL_PREFIXES:
            seg = seg[1:]
        if not seg or seg[0] in CONTROL_ENDS or seg[0] == "for":
            continue
        seg = _strip_wrappers(seg)
        if depth < 4:
            for nested in seg.nested:  # `env -S "..."` may be the whole segment
                result.extend(segments(nested, depth + 1))
        if not seg:
            continue
        result.append(seg)
        if depth >= 4:
            continue
        head = os.path.basename(seg[0])
        if head in SHELLS:
            prev = _strip_wrappers(raw[i - 1]) if i else None
            for script in _shell_scripts(seg, prev, operators[i]):
                result.extend(segments(script, depth + 1))
        elif head == "eval":
            result.extend(segments(" ".join(seg[1:]), depth + 1))
        for script in _launcher_scripts(seg):
            result.extend(segments(script, depth + 1))
    if depth < 4:
        for body in _heredoc_scripts(command):
            result.extend(segments(body, depth + 1))
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


def expand_braces(tok):
    """`.{env,}` -> [".env", "."], as the shell expands it before the command runs."""
    out, todo = [], [tok]
    while todo and len(out) + len(todo) < 64:
        t = todo.pop()
        m = _BRACES.search(t)
        if not m:
            out.append(t)
            continue
        for alt in m.group(0)[1:-1].split(","):
            todo.append(t[:m.start()] + alt + t[m.end():])
    return out + todo

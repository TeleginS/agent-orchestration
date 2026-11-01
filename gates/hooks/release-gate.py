#!/usr/bin/env python3
"""PreToolUse(Bash): publishing a release is the owner's gate.

Blocks every command matching a `release_commands` rule in gates.json:
  {"command": "fastlane"}                          any fastlane invocation
  {"command": "npm", "args": ["publish"]}          npm with the positional word `publish`
  {"command": "altool", "flag_prefix": "--upload"} altool with a flag starting --upload
`args` must appear in order among the non-flag arguments; when both `args` and
`flag_prefix` are given, both must hold. Launch prefixes are unwrapped first: `xcrun X`,
`bundle exec X`, `npx X`, `pnpm exec X`, `uvx X`, `uv run X`, `pipx run X`, `poetry run X`.
A version suffix (`npm@latest`) is ignored. When the arguments come from stdin through
`xargs`, the command name alone decides. With no rules, nothing is blocked.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from lib import block, read_payload, segments  # noqa: E402

MSG = (
    "Blocked by release-gate: %s. Publishing a release is the owner's gate. "
    "Build and verify locally; the owner runs the upload."
)
# launcher -> options that take a value
LAUNCHERS = {"xcrun": {"--sdk", "-sdk", "--toolchain", "-toolchain"}, "npx": {"-p", "--package", "-c", "--call"},
             "pnpx": set(), "bundle": set(), "bundler": set(), "pnpm": set(), "yarn": set(), "npm": set(),
             "uvx": {"--from", "--with", "-p", "--python"}, "uv": {"--with", "-p", "--python"},
             "pipx": {"--spec", "--python"}, "poetry": set()}
# launchers that run a command only after one of these words (`bundle exec`, `uv run`)
SUBWORDS = {"bundle": {"exec"}, "bundler": {"exec"}, "pnpm": {"exec", "dlx"}, "yarn": {"exec", "dlx"},
            "npm": {"exec"}, "uv": {"run"}, "pipx": {"run"}, "poetry": {"run"}}


def base_command(tok):
    """`./node_modules/.bin/npm@latest` -> `npm`."""
    name = os.path.basename(tok).lower()
    return name if name.startswith("@") else name.split("@", 1)[0]


def unwrap(seg):
    """`xcrun --sdk x altool ...` -> ["altool", ...]; `bundle exec fastlane` -> ["fastlane"]."""
    seg = list(seg)
    for _ in range(4):
        head = base_command(seg[0])
        subwords = SUBWORDS.get(head, set())
        if head not in LAUNCHERS:
            break
        rest, value_flags, i, sub_seen = seg[1:], LAUNCHERS[head], 0, False
        while i < len(rest):
            if rest[i] in subwords and not sub_seen:
                sub_seen = True
            elif rest[i].startswith("-"):
                i += 1 if rest[i] not in value_flags else 2
                continue
            else:
                break
            i += 1
        if i >= len(rest) or (subwords and not sub_seen):
            break
        seg = rest[i:]
    return seg


def subsequence(needle, haystack):
    it = iter(haystack)
    return all(word in it for word in needle)


def matches(rule, seg, stdin_args=False):
    if base_command(seg[0]) != rule["command"].lower():
        return False
    if stdin_args:
        return True  # the decisive arguments may arrive on stdin
    rest = seg[1:]
    if rule.get("args") and not subsequence(rule["args"], [a for a in rest if not a.startswith("-")]):
        return False
    if rule.get("flag_prefix") and not any(a.startswith(rule["flag_prefix"]) for a in rest):
        return False
    return True


def describe(rule):
    parts = [rule["command"]] + list(rule.get("args") or [])
    if rule.get("flag_prefix"):
        parts.append(rule["flag_prefix"] + "*")
    return " ".join(parts)


def main():
    payload = read_payload()
    command = (payload.get("tool_input") or {}).get("command") or ""
    rules = config.get()["release_commands"]
    if not rules:
        sys.exit(0)
    for seg in segments(command):
        inner = unwrap(seg)
        for rule in rules:
            if matches(rule, inner, seg.stdin_args):
                block(MSG % describe(rule))
    sys.exit(0)


if __name__ == "__main__":
    main()

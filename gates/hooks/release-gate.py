#!/usr/bin/env python3
"""PreToolUse(Bash): publishing a release is the owner's gate.

Blocks every command matching a `release_commands` rule in gates.json:
  {"command": "fastlane"}                          any fastlane invocation
  {"command": "npm", "args": ["publish"]}          npm with the positional word `publish`
  {"command": "altool", "flag_prefix": "--upload"} altool with a flag starting --upload
`args` must appear in order among the non-flag arguments; when both `args` and
`flag_prefix` are given, both must hold. Launch prefixes are unwrapped first:
`xcrun X`, `bundle exec X`, `npx X`, `pnpx X`. With no rules, nothing is blocked.
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
LAUNCHERS = {"xcrun": {"--sdk", "-sdk", "--toolchain", "-toolchain"}, "npx": {"-p", "--package"},
             "pnpx": set(), "bundle": set()}


def unwrap(seg):
    """`xcrun --sdk x altool ...` -> ["altool", ...]; `bundle exec fastlane` -> ["fastlane"]."""
    seg = list(seg)
    for _ in range(4):
        head = os.path.basename(seg[0]).lower()
        if head not in LAUNCHERS:
            break
        rest, value_flags, i = seg[1:], LAUNCHERS[head], 0
        while i < len(rest) and (rest[i].startswith("-") or (head == "bundle" and rest[i] == "exec")):
            i += 2 if rest[i] in value_flags else 1
        if i >= len(rest):
            break
        seg = rest[i:]
    return seg


def subsequence(needle, haystack):
    it = iter(haystack)
    return all(word in it for word in needle)


def matches(rule, seg):
    if os.path.basename(seg[0]).lower() != rule["command"].lower():
        return False
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
        seg = unwrap(seg)
        for rule in rules:
            if matches(rule, seg):
                block(MSG % describe(rule))
    sys.exit(0)


if __name__ == "__main__":
    main()

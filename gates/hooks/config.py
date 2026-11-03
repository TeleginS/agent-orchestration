"""Shared gate configuration: an explicit path, or gates.json next to these scripts.

Lookup order: $AGENT_GATES_CONFIG, then gates.json next to this file. A missing file
means defaults. A malformed file also falls back to defaults (with a stderr warning)
instead of blocking every tool call; `selftest.py` reports it.

Keys:
  protected_branches  branches only the owner merges into        [main, master]
    secret_names        basenames or fnmatch patterns agents may not open;
                        matching directory components protect children;
                        `<name>.<suffix>` variants match too        [.env]
  secret_allow        basenames that stay readable                [.env.example, .env.sample, .env.template]
  release_commands    commands that publish a release, e.g.
                      {"command": "fastlane"},
                      {"command": "npm", "args": ["publish"]},
                      {"command": "altool", "flag_prefix": "--upload"}   []
  allow_base_push     optional executable (relative to the repository root) called as
                      `<remote_sha> <local_sha> <branch>` for a fast-forward push to a
                      protected branch; exit 0 allows it. Same contract as the
                      `agent-gates.allowBasePush` setting of the git pre-push hook.
"""
import json
import os
import sys

DEFAULTS = {
    "protected_branches": ["main", "master"],
    "secret_names": [".env"],
    "secret_allow": [".env.example", ".env.sample", ".env.template"],
    "release_commands": [],
    "allow_base_push": None,
}
_LISTS = ("protected_branches", "secret_names", "secret_allow", "release_commands")


def config_path():
    explicit = os.environ.get("AGENT_GATES_CONFIG")
    if explicit:
        return explicit
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "gates.json")


def validate(data):
    """List of problems in a parsed config; empty when valid."""
    if not isinstance(data, dict):
        return ["top level must be a JSON object"]
    problems = []
    for key in _LISTS:
        if key in data and not isinstance(data[key], list):
            problems.append("%s must be a list" % key)
    for key in ("protected_branches", "secret_names", "secret_allow"):
        if isinstance(data.get(key), list) and not all(isinstance(v, str) and v for v in data[key]):
            problems.append("%s must contain non-empty strings" % key)
    rules = data.get("release_commands")
    for i, rule in enumerate(rules if isinstance(rules, list) else []):
        if not isinstance(rule, dict) or not isinstance(rule.get("command"), str) or not rule["command"]:
            problems.append("release_commands[%d] needs a non-empty \"command\"" % i)
            continue
        if "args" in rule and not (isinstance(rule["args"], list) and all(isinstance(a, str) for a in rule["args"])):
            problems.append("release_commands[%d].args must be a list of strings" % i)
        if "flag_prefix" in rule and not isinstance(rule["flag_prefix"], str):
            problems.append("release_commands[%d].flag_prefix must be a string" % i)
    allow = data.get("allow_base_push")
    if allow is not None and not isinstance(allow, str):
        problems.append("allow_base_push must be a string or null")
    return problems


def load(path=None):
    """(config, problems). Unknown keys (for example `_comment`) are ignored."""
    path = path or config_path()
    config = {k: (list(v) if isinstance(v, list) else v) for k, v in DEFAULTS.items()}
    try:
        with open(path) as fh:
            data = json.load(fh)
    except FileNotFoundError:
        return config, []
    except (OSError, ValueError) as exc:
        return config, ["%s: %s" % (path, exc)]
    problems = validate(data)
    if problems:
        return config, ["%s: %s" % (path, p) for p in problems]
    for key in DEFAULTS:
        if key in data:
            config[key] = data[key]
    return config, []


def get():
    config, problems = load()
    for p in problems:
        print("gates config ignored, using defaults: %s" % p, file=sys.stderr)
    return config

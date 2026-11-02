#!/usr/bin/env python3
"""PreToolUse(Bash): merging into a protected branch is the owner's gate.

Blocks `gh pr merge`, a merge through `gh api` (REST `pulls/<n>/merge` or the GraphQL merge
mutations), a push to a protected branch (explicit refspec, `HEAD`, or a bare `git push` while
on that branch), force pushes, `--mirror` and `--all`. Also blocks what would disable the
git-side guard: `git push --no-verify`, `core.hooksPath` overrides (`-c`, `git config`, the
`GIT_CONFIG_*` environment), alias definitions, and pushes whose arguments arrive from stdin
through `xargs`. Git aliases in the command or the repository config are resolved first.
Feature-branch pushes and `gh pr create/view` pass. A fast-forward push to a protected branch
passes only when the configured `allow_base_push` executable accepts it (see config.py).
"""
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from lib import Segment, block, expand_braces, positional, read_payload, segments  # noqa: E402

OWNER_MSG = (
    "Blocked by merge-gate: {what}. Merging into a protected branch is the owner's gate. "
    "Leave the PR open and report to the orchestrator or the owner; approval is a PR comment, "
    "and the owner merges."
)
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
GH_VALUE_FLAGS = {"-R", "--repo", "--hostname"}
GIT_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path", "--config-env"}
FORCE_FLAGS = {"--force", "-f", "--force-if-includes", "--mirror", "--all"}
# `git config` forms that only read; everything else with a guarded key is a write
CONFIG_READ_FLAGS = {"--get", "--get-all", "--get-regexp", "--get-urlmatch", "-l", "--list",
                     "--get-color", "--get-colorbool"}
CONFIG_WRITE_FLAGS = {"--unset", "--unset-all", "--add", "--replace-all", "-e", "--edit"}
CONFIG_SECTION_FLAGS = {"--remove-section", "--rename-section"}
CONFIG_VALUE_FLAGS = {"-f", "--file", "--blob", "-t", "--type", "--default"}
# Keys that define what git runs or what the pre-push hook permits.
GUARDED_KEYS = ("core.hookspath", "alias.", "agent-gates.allowbasepush", "agent-gates.protectedbranch")
REST_MERGE = re.compile(r"pulls/[^/\s]+/merge(?![\w-])")
GRAPHQL_MERGE = re.compile(r"mergePullRequest|enablePullRequestAutoMerge", re.I)
ENV_CONFIG = re.compile(r"\bgit_config_(parameters|key_\d+)=")
# Commands that handle these words as text; under any other unknown head (`$G ...`) a guard
# marker means a git invocation the parser could not resolve.
TEXT_COMMANDS = {"git", "gh", "grep", "egrep", "fgrep", "rg", "ag", "echo", "printf", "cat", "sed", "awk",
                 "less", "more", "head", "tail", "tee", "sort", "uniq", "wc", "diff", "cut", "tr", "jq"}
ALIAS_TOKEN = re.compile(r"^alias\.\w+(=|$)")
_builtins = None


def hidden_guard_marker(seg):
    """`--no-verify`, `core.hooksPath` or `alias.x=` under a head that is not git: `$G push --no-verify`."""
    if os.path.basename(seg[0]) in TEXT_COMMANDS:
        return None
    for tok in seg[1:]:
        low = tok.lower()
        if tok == "--no-verify" or "core.hookspath" in low or "agent-gates." in low or ALIAS_TOKEN.match(low):
            return tok
    return None


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd or None, capture_output=True, text=True, timeout=5)


def current_branch(cwd):
    try:
        return _git(cwd, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def builtins(cwd):
    """Names git resolves before aliases; an alias can never shadow one."""
    global _builtins
    if _builtins is None:
        try:
            _builtins = set(_git(cwd, "--list-cmds=builtins").stdout.split())
        except (OSError, subprocess.SubprocessError):
            _builtins = set()
    return _builtins


def split_git(seg):
    """Return (git -C dir, subcommand, subcommand args, {-c key: value}) or None."""
    args, workdir, inline, i = seg[1:], None, {}, 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            workdir = args[i + 1]
        if args[i] == "-c" and i + 1 < len(args):
            key, _, value = args[i + 1].partition("=")
            inline[key.lower()] = value
        elif args[i].startswith("-c") and len(args[i]) > 2:
            key, _, value = args[i][2:].partition("=")
            inline[key.lower()] = value
        i += 2 if args[i] in GIT_VALUE_FLAGS else 1
    if i >= len(args):
        return None
    return workdir, args[i], args[i + 1:], inline


def guard_change(sub, args, inline):
    """Describe a hook or alias redefinition in this git invocation, or return None."""
    for key in inline:
        if key.startswith(GUARDED_KEYS):
            return "git -c %s" % key
    if sub != "config" or any(a in CONFIG_READ_FLAGS for a in args):
        return None
    pos = positional(args, CONFIG_VALUE_FLAGS)
    section_op = any(a in CONFIG_SECTION_FLAGS for a in args)
    writes = section_op or any(a in CONFIG_WRITE_FLAGS for a in args) or len(pos) >= 2
    for p in pos:
        low = p.lower()
        if writes and (low.startswith(GUARDED_KEYS) or (section_op and low in {"alias", "core", "agent-gates"})):
            return "git config %s" % p
    return None


class Gate:
    def __init__(self, cfg):
        self.protected = list(cfg["protected_branches"])
        self.allow = cfg.get("allow_base_push")
        names = "|".join(re.escape(b) for b in self.protected) or r"(?!)"
        # `:<protected>` anywhere in the raw command, to catch refspecs the parser cannot resolve
        self.dst_pattern = re.compile(r":(refs/heads/)?(%s)(?![\w/.-])" % names)

    def protected_name(self, ref):
        if ref and ref.startswith("refs/heads/"):
            ref = ref[len("refs/heads/"):]
        return ref if ref in self.protected else None

    def allowed_base_push(self, remote, src, branch, cwd):
        """Ask the project's allow_base_push executable about src -> <remote>/<branch>.

        The base is the local remote-tracking ref (no fetch). An agent could rewrite that
        ref; the git pre-push hook checks against the real remote sha and closes the gap.
        """
        if not self.allow:
            return False
        if not remote or "/" in remote or ":" in remote:
            remote = "origin"
        try:
            root = _git(cwd, "rev-parse", "--show-toplevel").stdout.strip()
            base = _git(cwd, "rev-parse", "--verify", "-q", "refs/remotes/%s/%s^{commit}" % (remote, branch))
            head = _git(cwd, "rev-parse", "--verify", "-q", "%s^{commit}" % (src or "HEAD"))
            if not root or base.returncode or head.returncode:
                return False
            base_sha, head_sha = base.stdout.strip(), head.stdout.strip()
            if _git(cwd, "merge-base", "--is-ancestor", base_sha, head_sha).returncode != 0:
                return False
            script = self.allow if os.path.isabs(self.allow) else os.path.join(root, self.allow)
            run = subprocess.run([script, base_sha, head_sha, branch], cwd=root, stdin=subprocess.DEVNULL,
                                 capture_output=True, text=True, timeout=10)
            return run.returncode == 0
        except (OSError, subprocess.SubprocessError):
            return False

    def resolve_alias(self, sub, cwd):
        """The configured alias expansion for `git <sub>`, or None. Inline `-c alias.*` is blocked."""
        if sub in builtins(cwd):
            return None
        try:
            run = _git(cwd, "config", "--get", "alias.%s" % sub)
        except (OSError, subprocess.SubprocessError):
            return None
        return (run.stdout.strip() or None) if run.returncode == 0 else None

    def check_push(self, args, cwd, workdir, stdin_args=False):
        """Block a forbidden push; return the number of allowed refspecs of the form ...:<protected>."""
        if stdin_args:
            block(OWNER_MSG.format(what="git push with arguments from stdin (xargs)"))
        flags = [a for a in args if a.startswith("-")]
        for f in flags:
            if f == "--no-verify":
                block(OWNER_MSG.format(what="git push --no-verify (skips the pre-push hook)"))
            if f in FORCE_FLAGS or f.startswith("--force-with-lease"):
                block(OWNER_MSG.format(what="force push / push of all refs (%s)" % f))
            if re.match(r"^-[A-Za-z0-9]+$", f) and "f" in f[1:]:
                block(OWNER_MSG.format(what="force push (%s)" % f))
        pos = positional(args, PUSH_VALUE_FLAGS)
        # `--repo=x` / `--repo x` names the remote by flag: then every positional is a refspec
        remote_by_flag = any(a == "--repo" or a.startswith("--repo=") for a in args)
        refspecs = pos if remote_by_flag else pos[1:]
        remote = None if remote_by_flag else (pos[0] if pos else None)
        effective_cwd = os.path.join(cwd, workdir) if workdir and cwd else (workdir or cwd)
        branch, allowed = None, 0
        for spec in [s for r in refspecs for s in expand_braces(r)]:
            if spec.startswith("+"):
                block(OWNER_MSG.format(what="force push (refspec %s)" % spec))
            src, dst = spec.split(":", 1) if ":" in spec else (spec, spec)
            if dst == "HEAD":
                branch = branch or current_branch(effective_cwd)
                dst = branch
            target = self.protected_name(dst)
            if target:
                deleting = any(f in {"--delete", "-d"} or (re.match(r"^-[A-Za-z0-9]+$", f) and "d" in f[1:])
                               for f in flags)
                if src and not deleting and self.allowed_base_push(remote, src, target, effective_cwd):
                    allowed += bool(self.dst_pattern.search(spec))
                    continue
                block(OWNER_MSG.format(what="push to %s (%s)" % (target, spec)))
        if not refspecs:
            on = self.protected_name(current_branch(effective_cwd))
            if on:
                if self.allowed_base_push(remote, "HEAD", on, effective_cwd):
                    return 0
                block(OWNER_MSG.format(what="git push while on %s" % on))
        return allowed


def check_gh(seg):
    words = positional(seg[1:], GH_VALUE_FLAGS)
    if words[:2] == ["pr", "merge"]:
        block(OWNER_MSG.format(what="gh pr merge"))
    if words[:1] == ["api"]:
        if any(REST_MERGE.search(w) for w in seg):
            block(OWNER_MSG.format(what="PR merge through gh api"))
        if any(GRAPHQL_MERGE.search(w) for w in seg):
            block(OWNER_MSG.format(what="PR merge through the GraphQL API"))
    if words[:2] in (["alias", "set"], ["alias", "import"]):
        block(OWNER_MSG.format(what="gh alias definition (could hide a merge)"))
    if seg.stdin_args and words[:1] in (["pr"], ["api"]):
        block(OWNER_MSG.format(what="gh %s with arguments from stdin (xargs)" % words[0]))


def main():
    payload = read_payload()
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or ""
    gate = Gate(config.get())
    low = command.lower()
    if ENV_CONFIG.search(low) and ("hookspath" in low or "alias." in low or "agent-gates." in low):
        block(OWNER_MSG.format(what="git hooks or aliases redefined through GIT_CONFIG_* variables"))
    pushes, allowed, work, seen = 0, 0, list(segments(command)), 0
    while work and seen < 64:
        seg, seen = work.pop(0), seen + 1
        name = os.path.basename(seg[0])
        marker = hidden_guard_marker(seg)
        if marker:
            block(OWNER_MSG.format(what="%s in a command the gate cannot resolve (%s)" % (marker, seg[0])))
        if name == "gh":
            check_gh(seg)
        elif name == "git":
            parsed = split_git(seg)
            if not parsed:
                continue
            workdir, sub, args, inline = parsed
            what = guard_change(sub, args, inline)
            if what:
                block(OWNER_MSG.format(what="%s (redefines git hooks or commands)" % what))
            effective_cwd = os.path.join(cwd, workdir) if workdir and cwd else (workdir or cwd)
            alias = gate.resolve_alias(sub, effective_cwd)
            if alias:
                if alias.startswith("!"):
                    work.extend(segments(alias[1:]))
                    continue
                try:
                    expansion = shlex.split(alias)
                except ValueError:
                    expansion = alias.split()
                prefix = ["git"] + (["-C", workdir] if workdir else [])
                prefix += [tok for k, v in inline.items() for tok in ("-c", "%s=%s" % (k, v))]
                expanded = Segment(prefix + expansion + args)
                expanded.stdin_args = seg.stdin_args
                work.append(expanded)
                continue
            if sub == "push":
                pushes += 1
                allowed += gate.check_push(args, cwd, workdir, seg.stdin_args)
    # `$(cmd):main` and `$G push ...:main` do not parse into segments, so count `:<protected>`
    # in the raw command: every occurrence beyond the allowed refspecs blocks.
    if pushes and len(gate.dst_pattern.findall(command)) > allowed:
        block(OWNER_MSG.format(what="push to a protected branch (refspec ...:<branch>)"))
    sys.exit(0)


if __name__ == "__main__":
    main()

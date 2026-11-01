#!/usr/bin/env python3
"""PreToolUse(Bash): merging into a protected branch is the owner's gate.

Blocks `gh pr merge`, a merge through `gh api .../pulls/N/merge`, a push to a protected
branch (explicit refspec, `HEAD`, or a bare `git push` while on that branch), force
pushes, `--mirror` and `--all`. Feature-branch pushes and `gh pr create/view` pass.
A fast-forward push to a protected branch passes only when the configured
`allow_base_push` executable accepts it (see config.py).
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config  # noqa: E402
from lib import block, positional, read_payload, segments  # noqa: E402

OWNER_MSG = (
    "Blocked by merge-gate: {what}. Merging into a protected branch is the owner's gate. "
    "Leave the PR open and report to the orchestrator or the owner; approval is a PR comment, "
    "and the owner merges."
)
PUSH_VALUE_FLAGS = {"-o", "--push-option", "--repo", "--receive-pack", "--exec"}
GH_VALUE_FLAGS = {"-R", "--repo", "--hostname"}
GIT_VALUE_FLAGS = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}
FORCE_FLAGS = {"--force", "-f", "--force-if-includes", "--mirror", "--all"}


def _git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd or None, capture_output=True, text=True, timeout=5)


def current_branch(cwd):
    try:
        return _git(cwd, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def split_git(seg):
    """Return (git -C dir, subcommand, subcommand args) or None."""
    args, workdir, i = seg[1:], None, 0
    while i < len(args) and args[i].startswith("-"):
        if args[i] == "-C" and i + 1 < len(args):
            workdir = args[i + 1]
        i += 2 if args[i] in GIT_VALUE_FLAGS else 1
    if i >= len(args):
        return None
    return workdir, args[i], args[i + 1:]


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

    def check_push(self, args, cwd, workdir):
        """Block a forbidden push; return the number of allowed refspecs of the form ...:<protected>."""
        flags = [a for a in args if a.startswith("-")]
        for f in flags:
            if f in FORCE_FLAGS or f.startswith("--force-with-lease"):
                block(OWNER_MSG.format(what="force push / push of all refs (%s)" % f))
            if re.match(r"^-[A-Za-z]+$", f) and "f" in f[1:]:
                block(OWNER_MSG.format(what="force push (%s)" % f))
        pos = positional(args, PUSH_VALUE_FLAGS)
        # `--repo=x` / `--repo x` names the remote by flag: then every positional is a refspec
        remote_by_flag = any(a == "--repo" or a.startswith("--repo=") for a in args)
        refspecs = pos if remote_by_flag else pos[1:]
        remote = None if remote_by_flag else (pos[0] if pos else None)
        effective_cwd = os.path.join(cwd, workdir) if workdir and cwd else (workdir or cwd)
        branch, allowed = None, 0
        for spec in refspecs:
            if spec.startswith("+"):
                block(OWNER_MSG.format(what="force push (refspec %s)" % spec))
            src, dst = spec.split(":", 1) if ":" in spec else (spec, spec)
            if dst == "HEAD":
                branch = branch or current_branch(effective_cwd)
                dst = branch
            target = self.protected_name(dst)
            if target:
                deleting = any(f in {"--delete", "-d"} or (re.match(r"^-[A-Za-z]+$", f) and "d" in f[1:])
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


def main():
    payload = read_payload()
    command = (payload.get("tool_input") or {}).get("command") or ""
    cwd = payload.get("cwd") or ""
    gate = Gate(config.get())
    pushes, allowed = 0, 0
    for seg in segments(command):
        name = os.path.basename(seg[0])
        if name == "gh":
            words = positional(seg[1:], GH_VALUE_FLAGS)
            if len(words) >= 2 and words[0] == "pr" and words[1] == "merge":
                block(OWNER_MSG.format(what="gh pr merge"))
            if words[:1] == ["api"] and any(re.search(r"pulls/\d+/merge", w) for w in seg):
                block(OWNER_MSG.format(what="PR merge through gh api"))
        elif name == "git":
            parsed = split_git(seg)
            if parsed and parsed[1] == "push":
                pushes += 1
                allowed += gate.check_push(parsed[2], cwd, parsed[0])
    # `$(cmd):main` and `$G push ...:main` do not parse into segments, so count `:<protected>`
    # in the raw command: every occurrence beyond the allowed refspecs blocks.
    if pushes and len(gate.dst_pattern.findall(command)) > allowed:
        block(OWNER_MSG.format(what="push to a protected branch (refspec ...:<branch>)"))
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Self-test for the gate hooks: pipes JSON tool input into each script and checks the exit code.

Run before wiring the hooks into the host hook configuration, and after every change to them:
a broken PreToolUse hook blocks every later tool call.

    python3 gates/hooks/selftest.py        (exit 0: every case matched)

Expected exit: 2 = block, 0 = allow. Every case runs with its own config file, so the
result does not depend on the project's gates.json; that file is only validated.
The git pre-push cases run real pushes into throwaway bare remotes, never a real origin.
The pre-push script is found via $AGENT_GATES_PREPUSH, the library's gates/git/pre-push,
or <repo>/.githooks/pre-push; without one those cases are skipped.
"""
import atexit
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import config  # noqa: E402

tmp = os.path.realpath(tempfile.mkdtemp(prefix="gates-selftest-"))
atexit.register(shutil.rmtree, tmp, True)
# The hooks consult git (current branch, aliases); keep the user's own config out of the test.
GIT_ENV = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1",
               GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")


def sh(*args, cwd=tmp):
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, env=GIT_ENV)


def write(path, text, mode=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write(text)
    if mode:
        os.chmod(path, mode)
    return path


def write_json(name, data):
    return write(os.path.join(tmp, "configs", name), data if isinstance(data, str) else json.dumps(data))


# --- configs -------------------------------------------------------------------------
DEFAULT = write_json("default.json", {})
EXAMPLE = os.path.join(HERE, "gates.example.json")
if not os.path.exists(EXAMPLE):
    EXAMPLE = write_json("example.json", {
        "secret_names": [".env", "Secrets.xcconfig", "*.p8"],
        "secret_allow": [".env.example", ".env.sample", ".env.template", "Secrets.example.xcconfig"],
        "release_commands": [{"command": "fastlane"}, {"command": "iTMSTransporter"},
                             {"command": "altool", "flag_prefix": "--upload"},
                             {"command": "npm", "args": ["publish"]}, {"command": "twine", "args": ["upload"]}],
    })
ALLOW_YES = write_json("allow-yes.json", {"allow_base_push": "tools/allow.sh"})
ALLOW_NO = write_json("allow-no.json", {"allow_base_push": "tools/deny.sh"})
DEVELOP = write_json("develop.json", {"protected_branches": ["develop"]})
HOOK_DIR = write_json("hook-dir.json", {"secret_names": [".env", ".githooks"]})
BROKEN = write_json("broken.json", "{not json")
WRONG_TYPE = write_json("wrong-type.json", {"protected_branches": "develop"})


# --- repositories --------------------------------------------------------------------
def make_repo(name, branch="master"):
    path = os.path.join(tmp, name)
    os.makedirs(path)
    sh("git", "init", "-q", "-b", "master", cwd=path)
    write(os.path.join(path, "tools", "allow.sh"), "#!/bin/sh\nexit 0\n", 0o755)
    write(os.path.join(path, "tools", "deny.sh"), "#!/bin/sh\nexit 1\n", 0o755)
    sh("git", "add", "-A", cwd=path)
    sh("git", "commit", "-qm", "base", cwd=path)
    if branch != "master":
        sh("git", "checkout", "-qb", branch, cwd=path)
    return path


def make_pushed_repo(name, branch="master", ahead=True, amend=False, extra_branches=()):
    """Repo with a bare origin holding `branch`; then a local commit on top (ahead) or a rewrite (amend)."""
    bare = os.path.join(tmp, name + ".git")
    sh("git", "init", "-q", "--bare", bare)
    repo = make_repo(name, branch)
    sh("git", "remote", "add", "origin", bare, cwd=repo)
    for b in extra_branches:
        sh("git", "branch", b, cwd=repo)
        sh("git", "push", "-q", "origin", b, cwd=repo)
    sh("git", "push", "-q", "origin", branch, cwd=repo)
    if amend:
        sh("git", "commit", "--amend", "-qm", "rewritten", cwd=repo)
    elif ahead:
        write(os.path.join(repo, "change.txt"), "x\n")
        sh("git", "add", "-A", cwd=repo)
        sh("git", "commit", "-qm", "change", cwd=repo)
    return repo


on_master = make_repo("on-master")
on_main = make_repo("on-main", "main")
on_feature = make_repo("on-feature", "feature/x")
ff_master = make_pushed_repo("ff-master")
diverged_master = make_pushed_repo("diverged-master", amend=True)
# a clone whose config defines git aliases: `git p` is `git push`, `git pm` a shell alias
aliased = make_repo("aliased", "feature/x")
sh("git", "config", "alias.p", "push", cwd=aliased)
sh("git", "config", "alias.pm", "!git push origin master", cwd=aliased)
sh("git", "config", "alias.st", "status", cwd=aliased)

B = lambda cmd, cwd=on_feature: ("Bash", {"command": cmd}, cwd)
F = lambda tool, path: (tool, {"file_path": path}, on_feature)
G = lambda **tin: ("Grep", dict(pattern="KEY", **tin), on_feature)

MERGE, RELEASE, SECRETS = "merge-gate.py", "release-gate.py", "secrets-gate.py"

CASES = [
    # (hook, config, input, expected exit)
    (MERGE, DEFAULT, B("gh pr merge 1"), 2),
    (MERGE, DEFAULT, B("rtk gh pr merge 1 --squash"), 2),
    (MERGE, DEFAULT, B("git push origin master"), 2),
    (MERGE, DEFAULT, B("git push origin main"), 2),
    (MERGE, DEFAULT, B("git push origin HEAD:master"), 2),
    (MERGE, DEFAULT, B("git push origin HEAD:refs/heads/main"), 2),
    (MERGE, DEFAULT, B("git push", on_master), 2),
    (MERGE, DEFAULT, B("git push", on_main), 2),
    (MERGE, DEFAULT, B("git push origin", on_master), 2),
    (MERGE, DEFAULT, B("git push origin HEAD", on_master), 2),
    (MERGE, DEFAULT, B("git push --force origin feature/x"), 2),
    (MERGE, DEFAULT, B("git push -f origin feature/x"), 2),
    (MERGE, DEFAULT, B("git push -uf origin feature/x"), 2),
    (MERGE, DEFAULT, B("git push -4f origin feature/x"), 2),
    (MERGE, DEFAULT, B("git push --force-with-lease"), 2),
    (MERGE, DEFAULT, B("git push --mirror origin"), 2),
    (MERGE, DEFAULT, B("git push --all origin"), 2),
    (MERGE, DEFAULT, B("git push origin +feature/x"), 2),
    (MERGE, DEFAULT, B("rtk git push origin master"), 2),
    (MERGE, DEFAULT, B("cd x && gh pr merge 1 --squash"), 2),
    (MERGE, DEFAULT, B("echo ok; git push origin master"), 2),
    (MERGE, DEFAULT, B("git status | cat && git push origin main"), 2),
    (MERGE, DEFAULT, B('bash -c "git push origin master"'), 2),
    (MERGE, DEFAULT, B("eval git push origin main"), 2),
    (MERGE, DEFAULT, B("rtk git -C /tmp/x push origin master"), 2),
    (MERGE, DEFAULT, B("gh api -X PUT repos/o/r/pulls/5/merge"), 2),
    (MERGE, DEFAULT, B("PR=5; gh api -X PUT repos/o/r/pulls/$PR/merge"), 2),
    (MERGE, DEFAULT, B('gh api graphql -f query=\'mutation{mergePullRequest(input:{pullRequestId:"x"}){clientMutationId}}\''), 2),
    (MERGE, DEFAULT, B("gh api graphql -F id=x -f query='mutation($id:ID!){enablePullRequestAutoMerge(input:{pullRequestId:$id}){clientMutationId}}'"), 2),
    (MERGE, DEFAULT, B("gh alias set m 'pr merge'"), 2),
    (MERGE, DEFAULT, B("gh -R o/r pr merge 5"), 2),
    (MERGE, DEFAULT, B("gh --repo o/r pr merge 5"), 2),
    (MERGE, DEFAULT, B("gh pr --repo o/r merge 5"), 2),
    (MERGE, DEFAULT, B("gh pr --repo=o/r merge 5"), 2),
    (MERGE, DEFAULT, B("gh pr -Ro/r merge 5"), 2),
    (MERGE, DEFAULT, B("git push --repo=origin master"), 2),
    (MERGE, DEFAULT, B("git push --repo origin main"), 2),
    (MERGE, DEFAULT, B("git push origin $(git branch --show-current):master"), 2),
    (MERGE, DEFAULT, B("git push origin feature/x:refs/heads/main"), 2),
    (MERGE, DEFAULT, B("git push origin $(echo x):refs/heads/master"), 2),
    (MERGE, DEFAULT, B("git push origin HEAD:{master,}"), 2),
    # wrappers whose options take a value must not hide the command
    (MERGE, DEFAULT, B("sudo -u root git push origin master"), 2),
    (MERGE, DEFAULT, B("nice -n 10 git push origin master"), 2),
    (MERGE, DEFAULT, B("env -u FOO git push origin master"), 2),
    (MERGE, DEFAULT, B("timeout 30 git push origin master"), 2),
    (MERGE, DEFAULT, B("timeout -s KILL 30s git push origin master"), 2),
    (MERGE, DEFAULT, B('env -S "git push origin master"'), 2),
    (MERGE, DEFAULT, B("flock /tmp/lock git push origin master"), 2),
    # commands fed to a shell through stdin are commands
    (MERGE, DEFAULT, B("bash <<< 'git push origin master'"), 2),
    (MERGE, DEFAULT, B("echo 'git push origin master' | bash"), 2),
    (MERGE, DEFAULT, B("printf 'git push origin %s' master | sh -s"), 2),
    (MERGE, DEFAULT, B("bash <<'EOF'\ngit push origin master\nEOF"), 2),
    (MERGE, DEFAULT, B("cat <<EOF | bash\necho hi\ngit push origin master\nEOF"), 2),
    # xargs supplies arguments the parser cannot see
    (MERGE, DEFAULT, B("echo master | xargs git push origin"), 2),
    (MERGE, DEFAULT, B("echo master | xargs -I{} git push origin {}"), 2),
    (MERGE, DEFAULT, B("echo 5 | xargs -n1 gh pr merge"), 2),
    # disabling or redefining git's own guard is the owner's action
    (MERGE, DEFAULT, B("git push --no-verify origin feature/x"), 2),
    (MERGE, DEFAULT, B("git -c core.hooksPath=/dev/null push origin feature/x"), 2),
    (MERGE, DEFAULT, B("git config core.hooksPath /tmp/nohooks"), 2),
    (MERGE, DEFAULT, B("git config --unset core.hooksPath"), 2),
    (MERGE, DEFAULT, B("git config --global core.hookspath ''"), 2),
    (MERGE, DEFAULT, B("GIT_CONFIG_PARAMETERS=\"'core.hooksPath=/dev/null'\" git push origin feature/x"), 2),
    (MERGE, DEFAULT, B("GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/x git push origin feature/x"), 2),
    (MERGE, DEFAULT, B("git -c alias.p=push p origin master"), 2),
    (MERGE, DEFAULT, B("git -c alias.p=push p origin feature/x"), 2),
    (MERGE, DEFAULT, B("git config alias.p push"), 2),
    (MERGE, DEFAULT, B("git config --remove-section alias"), 2),
    (MERGE, DEFAULT, B("git p origin master", aliased), 2),
    (MERGE, DEFAULT, B("git p -f origin feature/x", aliased), 2),
    (MERGE, DEFAULT, B("git pm", aliased), 2),
    # an unresolved head (`$G`) carrying a guard marker is a hidden git invocation
    (MERGE, DEFAULT, B("G=git; $G push --no-verify origin main"), 2),
    (MERGE, DEFAULT, B("G=git; $G -c core.hooksPath=/dev/null push origin feature/x"), 2),
    (MERGE, DEFAULT, B("$G config alias.p push"), 2),
    (MERGE, DEFAULT, B("gh pr comment 5 --body 'hooks: core.hooksPath set, never use --no-verify'"), 0),
    (MERGE, DEFAULT, B("grep -rn hooksPath docs"), 0),
    (MERGE, DEFAULT, B("echo 'git push --no-verify'"), 0),
    (MERGE, DEFAULT, B("git -u origin feature/x 2>/dev/null; git push -u origin feature/x"), 0),
    (MERGE, DEFAULT, B("rtk git push origin feature/x"), 0),
    (MERGE, DEFAULT, B("git push", on_feature), 0),
    (MERGE, DEFAULT, B("git push origin master-fix"), 0),
    (MERGE, DEFAULT, B("git push origin maintenance"), 0),
    (MERGE, DEFAULT, B("git push --repo=origin feature/x"), 0),
    (MERGE, DEFAULT, B("git push origin --delete feature/old"), 0),
    (MERGE, DEFAULT, B("sudo -u root git push origin feature/x"), 0),
    (MERGE, DEFAULT, B("timeout 30 git push origin feature/x"), 0),
    (MERGE, DEFAULT, B("echo origin | xargs -n1 git fetch"), 0),
    (MERGE, DEFAULT, B("git p origin feature/x", aliased), 0),
    (MERGE, DEFAULT, B("git st", aliased), 0),
    (MERGE, DEFAULT, B("git config --get core.hooksPath"), 0),
    (MERGE, DEFAULT, B("git config core.hooksPath"), 0),
    (MERGE, DEFAULT, B("git config --list --show-origin"), 0),
    (MERGE, DEFAULT, B("git config user.name agent"), 0),
    (MERGE, DEFAULT, B("git commit --no-verify -m 'wip'"), 0),
    (MERGE, DEFAULT, B("gh -R o/r pr view 5"), 0),
    (MERGE, DEFAULT, B("gh --repo o/r pr create --title t"), 0),
    (MERGE, DEFAULT, B("gh pr create --title t --body 'run gh pr merge later'"), 0),
    (MERGE, DEFAULT, B("gh pr view 1"), 0),
    (MERGE, DEFAULT, B("gh api repos/o/r/pulls/5"), 0),
    (MERGE, DEFAULT, B("gh api graphql -f query='query{repository(owner:\"o\",name:\"r\"){pullRequest(number:5){merged}}}'"), 0),
    (MERGE, DEFAULT, B("git log master..HEAD"), 0),
    (MERGE, DEFAULT, B("git checkout main"), 0),
    (MERGE, DEFAULT, B("git commit -m \"$(cat <<'EOF'\ngh pr merge notes\nEOF\n)\""), 0),
    (MERGE, DEFAULT, B("cat <<'EOF'\ngit push origin master\nEOF"), 0),
    (MERGE, DEFAULT, B("cat <<'EOF' > notes.md\ngit push origin master\nEOF"), 0),
    (MERGE, DEFAULT, B("echo 'git push origin master'"), 0),
    (MERGE, DEFAULT, B("echo 'git push origin master' | cat"), 0),
    (MERGE, DEFAULT, B("bash -n script.sh"), 0),
    # allow_base_push: the project's executable decides a fast-forward push to a protected branch
    (MERGE, DEFAULT, B("git push origin master", ff_master), 2),
    (MERGE, ALLOW_NO, B("git push origin master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin master", ff_master), 0),
    (MERGE, ALLOW_YES, B("git push origin HEAD:master", ff_master), 0),
    (MERGE, ALLOW_YES, B("git push", ff_master), 0),
    (MERGE, ALLOW_YES, B("git push origin master && git push origin v1.0", ff_master), 0),
    (MERGE, ALLOW_YES, B("git push origin HEAD:master && git push origin v1.0", ff_master), 0),
    (MERGE, ALLOW_YES, B("git push origin master", diverged_master), 2),
    (MERGE, ALLOW_YES, B("git push --force origin master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin +master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin --delete master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin :master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push --no-verify origin master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin HEAD:master; $G push origin bad:master", ff_master), 2),
    (MERGE, ALLOW_YES, B("git push origin master && $(echo git) push origin bad:master", ff_master), 2),
    (MERGE, ALLOW_YES, B('git push origin HEAD:master && sh -c "$G push origin x:master"', ff_master), 2),
    # configured protected branches replace the defaults
    (MERGE, DEVELOP, B("git push origin develop"), 2),
    (MERGE, DEVELOP, B("git push origin HEAD:develop"), 2),
    (MERGE, DEVELOP, B("git push origin master"), 0),
    # an unreadable or invalid config falls back to the defaults, never to "allow"
    (MERGE, BROKEN, B("git push origin main"), 2),
    (MERGE, WRONG_TYPE, B("git push origin master"), 2),
    (MERGE, WRONG_TYPE, B("git push origin develop"), 0),

    # release gate: nothing is configured by default
    (RELEASE, DEFAULT, B("fastlane beta"), 0),
    (RELEASE, DEFAULT, B("npm publish"), 0),
    (RELEASE, BROKEN, B("fastlane beta"), 0),
    (RELEASE, EXAMPLE, B("xcrun altool --upload-app -f a.ipa"), 2),
    (RELEASE, EXAMPLE, B("rtk xcrun altool --upload-package a.ipa --apple-id 1"), 2),
    (RELEASE, EXAMPLE, B("xcrun --sdk iphoneos altool --upload-app -f a.ipa"), 2),
    (RELEASE, EXAMPLE, B("xcrun iTMSTransporter -m upload"), 2),
    (RELEASE, EXAMPLE, B("fastlane beta"), 2),
    (RELEASE, EXAMPLE, B("bundle exec fastlane beta"), 2),
    (RELEASE, EXAMPLE, B("bundler exec fastlane beta"), 2),
    (RELEASE, EXAMPLE, B("cd x && fastlane release"), 2),
    (RELEASE, EXAMPLE, B("npm publish"), 2),
    (RELEASE, EXAMPLE, B("npm --workspace pkg publish --access public"), 2),
    (RELEASE, EXAMPLE, B("npx npm publish"), 2),
    (RELEASE, EXAMPLE, B("npx --yes npm@latest publish"), 2),
    (RELEASE, EXAMPLE, B("npm exec -- npm publish"), 2),
    (RELEASE, EXAMPLE, B("pnpm exec fastlane beta"), 2),
    (RELEASE, EXAMPLE, B("yarn dlx npm publish"), 2),
    (RELEASE, EXAMPLE, B('bash -c "npm publish"'), 2),
    (RELEASE, EXAMPLE, B("bash <<< 'npm publish'"), 2),
    (RELEASE, EXAMPLE, B("echo 'npm publish' | sh"), 2),
    (RELEASE, EXAMPLE, B("sudo -u root npm publish"), 2),
    (RELEASE, EXAMPLE, B("timeout 600 fastlane beta"), 2),
    (RELEASE, EXAMPLE, B("echo publish | xargs npm"), 2),
    (RELEASE, EXAMPLE, B("twine upload dist/*"), 2),
    (RELEASE, EXAMPLE, B("uvx twine upload dist/*"), 2),
    (RELEASE, EXAMPLE, B("uv run twine upload dist/*"), 2),
    (RELEASE, EXAMPLE, B("pipx run twine upload dist/*"), 2),
    (RELEASE, EXAMPLE, B("poetry run twine upload dist/*"), 2),
    (RELEASE, EXAMPLE, B("xcrun altool --list-apps"), 0),
    (RELEASE, EXAMPLE, B("xcrun altool --validate-app -f a.ipa -t ios"), 0),
    (RELEASE, EXAMPLE, B("npm run build"), 0),
    (RELEASE, EXAMPLE, B("npm pack"), 0),
    (RELEASE, EXAMPLE, B("npm exec -- jest"), 0),
    (RELEASE, EXAMPLE, B("uv pip install twine"), 0),
    (RELEASE, EXAMPLE, B("echo x | xargs echo npm publish"), 0),
    (RELEASE, EXAMPLE, B("xcodebuild -project A.xcodeproj -scheme A -configuration Release archive"), 0),
    (RELEASE, EXAMPLE, B("grep altool README.md"), 0),
    (RELEASE, EXAMPLE, B("git commit -m 'remove fastlane'"), 0),
    (RELEASE, EXAMPLE, B("cat <<'EOF'\nfastlane beta\nEOF"), 0),
    (RELEASE, EXAMPLE, B("echo 'npm publish'"), 0),

    # secrets gate, default config: .env and its variants
    (SECRETS, DEFAULT, F("Edit", "/p/.env"), 2),
    (SECRETS, DEFAULT, F("Write", "/p/sub/.env.local"), 2),
    (SECRETS, DEFAULT, F("Read", "/p/.env.production"), 2),
    (SECRETS, DEFAULT, F("Read", "/p/.ENV"), 2),
    (SECRETS, DEFAULT, F("Read", "/p/.env.example"), 0),
    (SECRETS, DEFAULT, F("Read", "/p/.environment"), 0),
    (SECRETS, DEFAULT, F("Read", "/p/.envrc"), 0),
    (SECRETS, DEFAULT, F("Read", "/p/Secrets.xcconfig"), 0),
    (SECRETS, DEFAULT, ("NotebookEdit", {"notebook_path": "/p/.env"}, on_feature), 2),
    (SECRETS, DEFAULT, G(path="/p/.env"), 2),
    (SECRETS, DEFAULT, G(path="/p", glob=".env*"), 2),
    (SECRETS, DEFAULT, G(path="/p", glob="*.{env,local}"), 0),
    (SECRETS, DEFAULT, G(path="/p/src"), 0),
    (SECRETS, DEFAULT, G(path="/p", glob="*.py"), 0),
    (SECRETS, DEFAULT, B("grep KEY .env"), 2),
    (SECRETS, DEFAULT, B("rtk cat /p/.env"), 2),
    (SECRETS, DEFAULT, B("source .env"), 2),
    (SECRETS, DEFAULT, B("cat < .env"), 2),
    (SECRETS, DEFAULT, B("cat 0<.env"), 2),
    (SECRETS, DEFAULT, B("cat .env*"), 2),
    (SECRETS, DEFAULT, B("cat .en?"), 2),
    (SECRETS, DEFAULT, B("cat .{env,}"), 2),
    (SECRETS, DEFAULT, B("cat .en{v,vrc}"), 2),
    (SECRETS, DEFAULT, B("cat .ENV"), 2),
    (SECRETS, DEFAULT, B("echo hi && cat .env"), 2),
    (SECRETS, DEFAULT, B('bash -c "cat .env"'), 2),
    (SECRETS, DEFAULT, B("bash <<< 'cat .env'"), 2),
    (SECRETS, DEFAULT, B("echo 'cat .env' | sh"), 2),
    (SECRETS, DEFAULT, B("sudo -u root cat .env"), 2),
    (SECRETS, DEFAULT, B("grep -e KEY .env"), 2),
    (SECRETS, DEFAULT, B("grep -f .env other.txt"), 2),
    (SECRETS, DEFAULT, B("grep --file=.env other.txt"), 2),
    (SECRETS, DEFAULT, B("grep -efoo .env"), 2),
    (SECRETS, DEFAULT, B("grep -rne foo .env"), 2),
    (SECRETS, DEFAULT, B("grep -f.env other.txt"), 2),
    (SECRETS, DEFAULT, B("grep -r --include .env KEY ."), 2),
    (SECRETS, DEFAULT, B("grep -r --include=.env KEY ."), 2),
    (SECRETS, DEFAULT, B("rg -g .env KEY ."), 2),
    (SECRETS, DEFAULT, B("rg -g.env KEY ."), 2),
    (SECRETS, DEFAULT, B("rg --glob '.env*' KEY ."), 2),
    (SECRETS, DEFAULT, B("echo x >> .env"), 2),
    (SECRETS, DEFAULT, B("git show HEAD:.env"), 2),
    (SECRETS, DEFAULT, B("git show origin/main:config/.env.production"), 2),
    (SECRETS, DEFAULT, B("git cat-file -p HEAD:.env"), 2),
    (SECRETS, DEFAULT, B("cat .env.example"), 0),
    (SECRETS, DEFAULT, B("cat .environment"), 0),
    (SECRETS, DEFAULT, B("grep -efoo README.md"), 0),
    (SECRETS, DEFAULT, B("grep -rnefoo.env README.md"), 0),
    (SECRETS, DEFAULT, B("grep -r process.env src"), 0),
    (SECRETS, DEFAULT, B("grep -rn .env README.md"), 0),
    (SECRETS, DEFAULT, B("grep -r KEY --include '*.swift' ."), 0),
    (SECRETS, DEFAULT, B("rg -g '*.py' KEY ."), 0),
    (SECRETS, DEFAULT, B("grep foo *"), 0),
    (SECRETS, DEFAULT, B("cat *.*"), 0),
    (SECRETS, DEFAULT, B("cat *.md"), 0),
    (SECRETS, DEFAULT, B("cat {a,b}.txt"), 0),
    (SECRETS, DEFAULT, B("ls .env"), 0),
    (SECRETS, DEFAULT, B("ls -la .env*"), 0),
    (SECRETS, DEFAULT, B("echo $NODE_ENV .environment"), 0),
    (SECRETS, DEFAULT, B("echo 'DEBUG=1' > .env.example"), 0),
    (SECRETS, DEFAULT, B("git check-ignore .env"), 0),
    (SECRETS, DEFAULT, B("git log -- .env"), 2),
    (SECRETS, DEFAULT, B("git diff HEAD -- .env"), 2),
    (SECRETS, DEFAULT, B("git show HEAD:README.md"), 0),
    (SECRETS, BROKEN, F("Read", "/p/.env"), 2),
    # secrets gate, example config: extra names and patterns
    (SECRETS, EXAMPLE, F("Read", "/p/Secrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, F("Read", "/p/keys/AuthKey_ABC123.p8"), 2),
    (SECRETS, EXAMPLE, B("cat Secrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, B("cat SECRETS.XCCONFIG"), 2),
    (SECRETS, EXAMPLE, B("head -5 ./Secrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, B("cp Secrets.xcconfig /tmp/x"), 2),
    (SECRETS, EXAMPLE, B("cat S*"), 2),
    (SECRETS, EXAMPLE, B("cat *.xcconfig"), 2),
    (SECRETS, EXAMPLE, B("cat [S]ecrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, B("cat ./*.p8"), 2),
    (SECRETS, EXAMPLE, B("cat keys/AuthKey_*.p8"), 2),
    (SECRETS, EXAMPLE, B("grep Secrets.xcconfig Secrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, B("grep -rnefoo Secrets.xcconfig"), 2),
    (SECRETS, EXAMPLE, F("Read", "/p/Secrets.example.xcconfig"), 0),
    (SECRETS, EXAMPLE, B("cat Secrets.example.xcconfig"), 0),
    (SECRETS, EXAMPLE, B("cat *.*"), 0),
    (SECRETS, EXAMPLE, B("cat *.swift"), 0),
    (SECRETS, EXAMPLE, B('grep -r "Secrets.xcconfig" docs'), 0),
    (SECRETS, EXAMPLE, B("git check-ignore Secrets.xcconfig"), 0),
]


def patch(*lines):
    return ("apply_patch", {"command": "\n".join(("*** Begin Patch", *lines, "*** End Patch"))}, on_feature)


# Codex emits apply_patch in tool_input.command, including when matched as Edit/Write.
CASES.extend([
    (SECRETS, DEFAULT, patch("*** Add File: .env", "+KEY=example"), 2),
    (SECRETS, DEFAULT, patch("*** Update File: sub/.env.local", "@@", "-old", "+new"), 2),
    (SECRETS, DEFAULT, patch("*** Delete File: /project/.env.production"), 2),
    (SECRETS, DEFAULT, patch("*** Update File: allowed.txt", "*** Move to: .env"), 2),
    (SECRETS, DEFAULT, patch("*** Update File: .env", "*** Move to: allowed.txt"), 2),
    (SECRETS, DEFAULT, patch("*** Add File: C:\\project\\.env.local", "+KEY=example"), 2),
    (SECRETS, EXAMPLE, patch("*** Update File: keys/AuthKey_123.p8", "@@", "+x"), 2),
    (SECRETS, DEFAULT, patch("*** Add File: .env.example", "+KEY=example"), 0),
    (SECRETS, EXAMPLE, patch("*** Update File: Secrets.example.xcconfig", "@@", "+x"), 0),
    (SECRETS, DEFAULT, patch("*** Update File: docs.md", "@@", "+*** Delete File: .env"), 0),
    (SECRETS, DEFAULT, patch("*** Add File: src/ordinary.py", "+x = '.env'"), 0),
    (SECRETS, DEFAULT, patch("*** Add File: good.txt", "+x", "*** Delete File: .env"), 2),
    (SECRETS, DEFAULT, ("apply_patch", {}, on_feature), 2),
])

# Regression cases for commands hidden in shell control flow, launcher command strings,
# git guard configuration, and secret-bearing Git output or redirections.
CASES.extend([
    (MERGE, DEFAULT, B("if true; then gh pr merge 1; fi"), 2),
    (MERGE, DEFAULT, B("if ! gh pr merge 1; then echo done; fi"), 2),
    (MERGE, DEFAULT, B("if git push origin main; then echo done; fi"), 2),
    (MERGE, DEFAULT, B("while true; do gh pr merge 1; done"), 2),
    (MERGE, DEFAULT, B("until true; do git push origin main; done"), 2),
    (MERGE, DEFAULT, B("for x in a b; do gh pr merge 1; done"), 2),
    (MERGE, DEFAULT, B("if true\nthen\n gh pr merge 1\nfi"), 2),
    (MERGE, DEFAULT, B("git config agent-gates.allowBasePush /usr/bin/true"), 2),
    (MERGE, DEFAULT, B("git config --unset agent-gates.protectedBranch"), 2),
    (MERGE, DEFAULT, B("git config --remove-section agent-gates"), 2),
    (MERGE, DEFAULT, B("git -cagent-gates.allowBasePush=/usr/bin/true push origin feature/x"), 2),
    (MERGE, DEFAULT, B("git -ccore.hooksPath=/dev/null push origin feature/x"), 2),
    (MERGE, DEFAULT, B("GIT_CONFIG_KEY_0=agent-gates.allowBasePush git push origin feature/x"), 2),
    (MERGE, DEFAULT, B("git config --get agent-gates.allowBasePush"), 0),
    (MERGE, DEFAULT, B('echo "then gh pr merge 1"'), 0),
    (RELEASE, EXAMPLE, B("if true; then npm publish; fi"), 2),
    (RELEASE, EXAMPLE, B('npx --yes --package npm -c "npm publish"'), 2),
    (RELEASE, EXAMPLE, B('npx --call="npm publish"'), 2),
    (RELEASE, EXAMPLE, B('npm exec --call="npm publish"'), 2),
    (RELEASE, EXAMPLE, B('echo "then npm publish"'), 0),
    (RELEASE, EXAMPLE, B('npx --package npm echo safe'), 0),
    (SECRETS, DEFAULT, B("git log -p -- .env"), 2),
    (SECRETS, DEFAULT, B("git status -- .env"), 0),
    (SECRETS, DEFAULT, B("git ls-files -- .env"), 0),
    (SECRETS, DEFAULT, B("ls > .env"), 2),
    (SECRETS, DEFAULT, B("test -f harmless 2>.env"), 2),
    (SECRETS, DEFAULT, B("if true; then ls > .env; fi"), 2),
    (SECRETS, HOOK_DIR, B("cat .githooks/pre-push"), 2),
    (SECRETS, HOOK_DIR, F("Read", "/p/.githooks/pre-push"), 2),
    (SECRETS, HOOK_DIR, patch("*** Update File: .githooks/pre-push", "@@", "+x"), 2),
    (SECRETS, HOOK_DIR, F("Read", "/p/.env.example"), 0),
])


def label(code):
    return "block" if code == 2 else ("allow" if code == 0 else "ERR%d" % code)


failed = 0
print("%-15s %-12s %-6s %-6s %s" % ("hook", "config", "want", "got", "input"))
for hook, cfg, (tool, tin, cwd), want in CASES:
    payload = {"hook_event_name": "PreToolUse", "tool_name": tool, "tool_input": tin, "cwd": cwd}
    env = dict(GIT_ENV, AGENT_GATES_CONFIG=cfg)
    run = subprocess.run([sys.executable, os.path.join(HERE, hook)], input=json.dumps(payload),
                         capture_output=True, text=True, timeout=15, env=env)
    ok = run.returncode == want
    failed += not ok
    desc = (tin.get("command") or tin.get("file_path") or tin.get("notebook_path")
            or (tin.get("path") and "%s glob=%s" % (tin["path"], tin.get("glob"))) or "<missing input>")
    desc = desc.replace("\n", "\\n")
    where = " [cwd=%s]" % os.path.basename(cwd) if tool == "Bash" and cwd != on_feature else ""
    print("%-15s %-12s %-6s %-6s %s%s%s" % (hook[:-3], os.path.basename(cfg)[:-5], label(want),
                                           label(run.returncode), desc[:64], where,
                                           "" if ok else "   <-- MISMATCH"))
    if not ok and run.stderr.strip():
        print("   stderr: " + run.stderr.strip().splitlines()[-1][:160])
    if want == 2 and ok and not run.stderr.strip():
        failed += 1
        print("   ^ blocked without a message")
    if want == 2 and ok and hook == MERGE and "owner" not in run.stderr:
        failed += 1
        print("   ^ message does not name the owner")
total = len(CASES)


# --- git pre-push: real pushes into throwaway bare remotes ---------------------------
def find_prepush():
    candidates = [os.environ.get("AGENT_GATES_PREPUSH"),
                  os.path.join(HERE, "..", "git", "pre-push")]
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=HERE,
                             capture_output=True, text=True, timeout=5).stdout.strip()
        if top:
            candidates.append(os.path.join(top, ".githooks", "pre-push"))
    except (OSError, subprocess.SubprocessError):
        pass
    for c in candidates:
        if c and os.path.isfile(c):
            return os.path.realpath(c)
    return None


prepush = find_prepush()
if prepush:
    hooks_dir = os.path.join(tmp, "githooks")
    os.makedirs(hooks_dir)
    dst = os.path.join(hooks_dir, "pre-push")
    with open(prepush) as src_fh:
        write(dst, src_fh.read(), 0o755)

    def push_repo(name, settings=(), **kw):
        repo = make_pushed_repo(name, **kw)
        sh("git", "config", "core.hooksPath", hooks_dir, cwd=repo)
        for key, value in settings:
            sh("git", "config", "--add", key, value, cwd=repo)
        return repo

    ALLOW = ("agent-gates.allowBasePush", "tools/allow.sh")
    DENY = ("agent-gates.allowBasePush", "tools/deny.sh")
    PUSHES = [
        # (description, repo factory, push args, expected: 0 allow / 1 block)
        ("ff push to master, no allow script", lambda: push_repo("pp-ff"), ["origin", "master"], 1),
        ("ff push to master, allow script exit 0", lambda: push_repo("pp-allow", [ALLOW]), ["origin", "master"], 0),
        ("ff push to master, allow script exit 1", lambda: push_repo("pp-deny", [DENY]), ["origin", "master"], 1),
        ("forced rewrite of master, allow script exit 0",
         lambda: push_repo("pp-rewrite", [ALLOW], amend=True), ["-f", "origin", "master"], 1),
        ("ff push of a feature branch", lambda: push_repo("pp-feat", branch="feature/x"), ["origin", "feature/x"], 0),
        ("new feature branch", lambda: push_repo("pp-new", ahead=False), ["origin", "HEAD:refs/heads/feature/y"], 0),
        ("force push of a feature branch",
         lambda: push_repo("pp-force", branch="feature/x", amend=True), ["-f", "origin", "feature/x"], 1),
        ("delete a feature branch",
         lambda: push_repo("pp-del", extra_branches=["feature/old"]), ["origin", "--delete", "feature/old"], 0),
        ("protectedBranch=develop: push master",
         lambda: push_repo("pp-dev-m", [("agent-gates.protectedBranch", "develop")]), ["origin", "master"], 0),
        ("protectedBranch=develop: push develop",
         lambda: push_repo("pp-dev-d", [("agent-gates.protectedBranch", "develop")]),
         ["origin", "HEAD:refs/heads/develop"], 1),
    ]
    for desc, factory, args, want in PUSHES:
        repo = factory()
        run = subprocess.run(["git", "push", "-q", *args], cwd=repo, capture_output=True, text=True,
                             timeout=30, env=GIT_ENV)
        ok = (run.returncode == 0) == (want == 0)
        failed += not ok
        print("%-15s %-12s %-6s %-6s %s%s" % ("pre-push", "git config", "allow" if want == 0 else "block",
                                              "allow" if run.returncode == 0 else "block", desc,
                                              "" if ok else "   <-- MISMATCH"))
        if want and ok and "pre-push:" not in run.stderr:
            failed += 1
            print("   ^ rejected, but not by the pre-push hook: " + run.stderr.strip()[:160])
    total += len(PUSHES)
else:
    print("\npre-push: script not found, cases skipped (set AGENT_GATES_PREPUSH)")

# --- the project's own config -------------------------------------------------------
installed = config.config_path()
if os.environ.get("AGENT_GATES_CONFIG") or os.path.exists(installed):
    _, problems = config.load(installed)
    total += 1
    failed += bool(problems)
    print("\n" + ("; ".join(problems) if problems else "config %s: valid" % installed))
else:
    print("\nno config at %s: defaults apply, so the release gate blocks nothing until gates.json exists"
          % installed)

print("\n%d cases, %d failed" % (total, failed))
sys.exit(1 if failed else 0)

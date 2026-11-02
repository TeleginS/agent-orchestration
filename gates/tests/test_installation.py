"""Exercise the published host wiring against installed scripts in real git projects.

Run: python3 -m unittest discover -s gates/tests -v
No target commands are executed: only the hooks deciding whether to allow them.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest


LIBRARY = Path(__file__).resolve().parents[2]


class InstalledGates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="agent gates installation ")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.env = {k: v for k, v in os.environ.items()
                    if k not in {"AGENT_GATES_CONFIG", "CLAUDE_PROJECT_DIR"}}
        self.env.update(CLAUDE_PROJECT_DIR=str(self.project),
                        GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM="1")
        subprocess.run(["git", "init", "-q", str(self.project)], check=True, env=self.env)
        self.groups = {}
        for host, wiring in (
            ("codex", "adapters/codex/hooks.example.json"),
            ("claude", "adapters/claude-code/hooks/settings.example.json"),
        ):
            hooks = self.project / ("." + host) / "hooks"
            hooks.mkdir(parents=True)
            for script in (LIBRARY / "gates/hooks").glob("*.py"):
                shutil.copy2(script, hooks / script.name)
            shutil.copy2(LIBRARY / "gates/hooks/gates.example.json", hooks / "gates.json")
            self.groups[host] = json.loads((LIBRARY / wiring).read_text())["hooks"]["PreToolUse"]

    def invoke(self, command, payload, env=None):
        return subprocess.run(command, shell=True, cwd=self.project,
                              input=json.dumps(payload), text=True, capture_output=True,
                              env=env or self.env, timeout=15)

    def check_wiring(self, host, tool, args, blocked):
        payload = {"hook_event_name": "PreToolUse", "session_id": "test",
                   "cwd": str(self.project), "tool_name": tool, "tool_input": args}
        runs = [self.invoke(hook["command"], payload)
                for group in self.groups[host] if re.search(group["matcher"], tool)
                for hook in group["hooks"]]
        self.assertTrue(runs, "The tool must match at least one configured gate")
        self.assertTrue(all(r.returncode in (0, 2) for r in runs),
                        [r.stderr for r in runs])
        self.assertEqual(any(r.returncode == 2 for r in runs), blocked,
                         [r.stderr for r in runs])
        for run in runs:
            if run.returncode == 2:
                self.assertIn("Blocked by", run.stderr)

    def test_shell_wiring_in_both_hosts(self):
        for host in self.groups:
            for command, blocked in (
                ("gh pr merge 123 --squash", True),
                ("if true; then gh pr merge 123; fi", True),
                ("gh api -X PUT repos/o/r/pulls/123/merge", True),
                ("git push origin HEAD:main", True),
                ("git config agent-gates.allowBasePush /usr/bin/true", True),
                ("npm publish", True),
                ("if true; then npm publish; fi", True),
                ('npx --package npm -c "npm publish"', True),
                ("cat .env.local", True),
                ("git diff -- .env", True),
                ("ls > .env", True),
                ("gh pr view 123", False),
                ("git push origin HEAD:feature/work", False),
                ("npm run build", False),
                ("cat .env.example", False),
                ("git status -- .env", False),
            ):
                with self.subTest(host=host, command=command):
                    self.check_wiring(host, "Bash", {"command": command}, blocked)

    def test_codex_patch_wiring(self):
        for header, blocked in (
            ("*** Add File: .env", True),
            ("*** Delete File: .env.production", True),
            ("*** Update File: x.txt\n*** Move to: .env", True),
            ("*** Update File: .env\n*** Move to: x.txt", True),
            ("*** Add File: .env.example", False),
            ("*** Add File: source.py", False),
        ):
            with self.subTest(header=header):
                self.check_wiring("codex", "apply_patch",
                                  {"command": "*** Begin Patch\n" + header + "\n*** End Patch"}, blocked)

    def test_secret_directory_wiring(self):
        for host in self.groups:
            config = self.project / ("." + host) / "hooks/gates.json"
            config.write_text(json.dumps({"secret_names": [".env", ".githooks"]}))
            with self.subTest(host=host):
                self.check_wiring(host, "Bash", {"command": "cat .githooks/pre-push"}, True)
                if host == "claude":
                    self.check_wiring(host, "Read", {"file_path": str(self.project / ".githooks/pre-push")},
                                      True)
                else:
                    self.check_wiring(host, "apply_patch", {"command":
                                      "*** Begin Patch\n*** Update File: .githooks/pre-push\n@@\n+x\n*** End Patch"}, True)

    def test_claude_file_wiring(self):
        for tool, key in (("Read", "file_path"), ("Edit", "file_path"), ("Write", "file_path"),
                          ("MultiEdit", "file_path"), ("NotebookEdit", "notebook_path"), ("Grep", "path")):
            with self.subTest(tool=tool):
                self.check_wiring("claude", tool, {key: str(self.project / ".env"), "pattern": "KEY"}, True)
        self.check_wiring("claude", "Grep", {"pattern": "KEY", "path": str(self.project), "glob": ".env*"}, True)
        self.check_wiring("claude", "Grep", {"pattern": "KEY", "path": str(self.project / "src")}, False)

    def test_adjacent_config_is_host_specific(self):
        # A Claude project variable must not redirect Codex to Claude's rules.
        config = self.project / ".codex/hooks/gates.json"
        config.write_text(json.dumps({"protected_branches": ["develop"]}))
        self.check_wiring("codex", "Bash", {"command": "git push origin develop"}, True)
        self.check_wiring("codex", "Bash", {"command": "git push origin main"}, False)
        self.check_wiring("claude", "Bash", {"command": "git push origin main"}, True)

    def test_explicit_config_wins(self):
        override = self.project / "custom rules.json"
        override.write_text(json.dumps({"release_commands": [{"command": "custom-publish"}]}))
        env = dict(self.env, AGENT_GATES_CONFIG=str(override))
        for host in self.groups:
            with self.subTest(host=host):
                script = self.project / ("." + host) / "hooks/release-gate.py"
                run = subprocess.run([sys.executable, str(script)], cwd=self.project,
                                     input=json.dumps({"tool_name": "Bash", "tool_input":
                                                       {"command": "custom-publish"}}),
                                     text=True, capture_output=True, env=env, timeout=15)
                self.assertEqual(run.returncode, 2, run.stderr)

    def test_legacy_library_entry_points(self):
        for name, command in (("merge-gate.py", "gh pr merge 1"),
                              ("release-gate.py", "npm publish"),
                              ("secrets-gate.py", "cat .env")):
            with self.subTest(script=name):
                script = LIBRARY / "adapters/claude-code/hooks" / name
                run = subprocess.run([sys.executable, str(script)], cwd=self.project,
                                     input=json.dumps({"tool_name": "Bash", "tool_input":
                                                       {"command": command}}),
                                     text=True, capture_output=True, env=self.env, timeout=15)
                self.assertEqual(run.returncode, 2, run.stderr)


if __name__ == "__main__":
    unittest.main()

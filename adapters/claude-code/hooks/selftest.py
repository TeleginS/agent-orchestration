#!/usr/bin/env python3
"""Compatibility entry point; install the shared scripts from gates/hooks/ instead."""
import os
from pathlib import Path
import runpy

here = Path(__file__).resolve()
project = os.environ.get("CLAUDE_PROJECT_DIR")
local_config = Path(project) / ".claude/hooks/gates.json" if project else here.with_name("gates.json")
if local_config.is_file():
    os.environ.setdefault("AGENT_GATES_CONFIG", str(local_config))
runpy.run_path(str(here.parents[3] / "gates/hooks" / here.name), run_name="__main__")

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(root: Path, *args: str) -> dict:
    env = dict(os.environ, RAPP_PROJECTS_ROOT=str(root))
    result = subprocess.run(
        [sys.executable, "-m", "rapp_projects.cli", *args],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return json.loads(result.stdout)


def test_cli_open_checkpoint_board_and_resume(tmp_path: Path) -> None:
    root = tmp_path / "control"
    assert run_cli(
        root,
        "open",
        "--json",
        json.dumps({
            "project": "cli",
            "title": "CLI",
            "goal": "Work anywhere",
            "owner": "example",
            "origin": "test",
        }),
    )["status"] == "ok"
    assert run_cli(
        root,
        "punchin",
        "--json",
        json.dumps({
            "project": "cli",
            "agent": "hermes",
            "runtime": "hermes",
            "session_id": "h1",
            "capabilities": ["files", "shell"],
            "location": "/workspace",
            "intent": "checkpoint",
            "role": "builder",
        }),
    )["status"] == "ok"
    assert run_cli(
        root,
        "checkpoint",
        "--json",
        json.dumps({
            "project": "cli",
            "agent": "hermes",
            "runtime": "hermes",
            "session_id": "h1",
            "summary": "Started",
            "completed": [],
            "in_progress": "implementation",
            "next_action": "continue",
            "resume_prompt": "Continue implementation.",
            "cwd": "/workspace",
            "repository": "https://github.com/example/cli",
            "branch": "main",
            "head": "c" * 40,
            "dirty_paths": [],
            "commands": [],
            "artifacts": [],
        }),
    )["status"] == "ok"
    resume = run_cli(root, "resume", "--json", '{"project":"cli"}')
    assert resume["checkpoint"]["resume"]["prompt"] == "Continue implementation."
    board = run_cli(root, "board", "--json", "{}")
    assert Path(board["board"]).is_file()


def test_brainstem_agent_loads_without_brainstem_package(tmp_path: Path) -> None:
    env = dict(os.environ, RAPP_PROJECTS_ROOT=str(tmp_path / "control"))
    result = subprocess.run(
        [sys.executable, "agents/rapp_projects_agent.py"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    assert json.loads(result.stdout)["status"] == "ok"

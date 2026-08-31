from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from rapp_projects.core import (
    Actor,
    Checkpoint,
    PROJECT_KINDS,
    ProjectError,
    build_project_frame,
    build_project_rappid,
    verify_project_frames,
)


UTC0 = "2026-08-31T00:00:00.000Z"
UTC1 = "2026-08-31T00:00:01.000Z"


def actor() -> Actor:
    return Actor(
        id="claude-code",
        runtime="claude-code",
        session_id="session-1",
        capabilities=("files", "shell", "tests"),
    )


def test_all_public_kinds_use_rapp_grammar() -> None:
    assert PROJECT_KINDS == (
        "project.genesis",
        "work.punchin",
        "work.heartbeat",
        "work.checkpoint",
        "work.status",
        "work.handoff",
        "work.takeover",
        "work.punchout",
        "cell.policy",
        "cell.cycle",
        "cell.absorb",
        "project.verify",
    )
    assert all(kind.count(".") == 1 for kind in PROJECT_KINDS)


def test_project_stream_round_trip() -> None:
    stream_id = build_project_rappid("example", "portable", b"seed")
    first = build_project_frame(
        kind="project.genesis",
        stream_id=stream_id,
        seq=0,
        utc=UTC0,
        payload={
            "project": "portable",
            "title": "Portable",
            "goal": "Cross runtime handoff",
            "owner": "example",
            "origin": "test",
            "visibility": "local",
        },
        prev=None,
    )
    second = build_project_frame(
        kind="work.punchin",
        stream_id=stream_id,
        seq=1,
        utc=UTC1,
        payload={
            "project": "portable",
            "actor": actor().as_payload(),
            "location": "/workspace",
            "intent": "continue",
            "role": "builder",
            "lease_expires_utc": "2026-08-31T01:00:00.000Z",
        },
        prev=first["payload_hash"],
    )
    verified = verify_project_frames([first, second], stream_id)
    assert verified.head.seq == 1


def test_checkpoint_requires_exact_resume_state() -> None:
    checkpoint = Checkpoint(
        summary="Tests are red at the import gate.",
        completed=("protocol schema",),
        in_progress="egg divergence handling",
        next_action="fix prefix verification",
        resume_prompt="Continue from the failing divergence test.",
        cwd="/workspace",
        repository="https://github.com/example/project",
        branch="feature/projects",
        head="a" * 40,
        dirty_paths=("src/core.py",),
        commands=("python -m pytest",),
        artifacts=(),
    )
    payload = checkpoint.as_payload()
    assert payload["resume"]["prompt"].startswith("Continue")
    assert payload["workspace"]["dirty_paths"] == ["src/core.py"]


def test_unknown_project_kind_is_refused() -> None:
    with pytest.raises(ProjectError):
        build_project_frame(
            kind="work.magic",
            stream_id=build_project_rappid("example", "bad", b"seed"),
            seq=0,
            utc=UTC0,
            payload={},
            prev=None,
        )

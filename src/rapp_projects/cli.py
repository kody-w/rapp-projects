"""Universal JSON CLI for RAPP Projects."""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

from .core import Actor, ProjectError, ProjectStore


ACTIONS = (
    "open", "punchin", "heartbeat", "checkpoint", "status", "handoff",
    "takeover", "punchout", "resume", "board", "export", "import",
    "verify", "absorb", "policy", "cycle", "due", "approve",
)


def _committed(store: ProjectStore, frame: dict[str, object], **extra):
    return {
        "status": "ok",
        "committed": True,
        "frame_hash": frame["frame_hash"],
        "projection_warning": store.last_projection_warning,
        **extra,
    }


def _actor(values: dict[str, object], prefix: str = "") -> Actor:
    key = lambda name: prefix + name
    return Actor(
        id=str(values.get(key("agent")) or values.get(key("id")) or "unknown-ai"),
        runtime=str(values.get(key("runtime")) or "unknown-runtime"),
        session_id=str(values.get(key("session_id")) or "unknown-session"),
        capabilities=tuple(values.get(key("capabilities")) or ()),
        model=(
            str(values[key("model")])
            if values.get(key("model")) is not None else None
        ),
        host=(
            str(values[key("host")])
            if values.get(key("host")) is not None else socket.gethostname()
        ),
    )


def dispatch(store: ProjectStore, action: str, values: dict[str, object]):
    project = str(values.get("project") or "")
    if action == "open":
        frame = store.open(
            project,
            title=str(values.get("title") or project),
            goal=str(values.get("goal") or ""),
            owner=str(values.get("owner") or "unassigned"),
            origin=str(values.get("origin") or "cli"),
            visibility=str(values.get("visibility") or "local"),
        )
        return _committed(store, frame, project=project)
    if action == "punchin":
        frame = store.punchin(
            project,
            _actor(values),
            location=str(values.get("location") or os.getcwd()),
            intent=str(values.get("intent") or "continue"),
            role=str(values.get("role") or "worker"),
            lease_seconds=int(values.get("lease_seconds") or 3600),
        )
        return _committed(store, frame)
    if action == "heartbeat":
        frame = store.heartbeat(
            project,
            _actor(values),
            status=str(values.get("status") or "working"),
            lease_seconds=int(values.get("lease_seconds") or 3600),
        )
        return _committed(store, frame)
    if action == "checkpoint":
        frame = store.checkpoint(
            project,
            _actor(values),
            summary=str(values.get("summary") or ""),
            completed=values.get("completed") or [],
            in_progress=str(values.get("in_progress") or ""),
            next_action=str(values.get("next_action") or ""),
            resume_prompt=str(values.get("resume_prompt") or ""),
            cwd=str(values.get("cwd") or os.getcwd()),
            repository=str(values.get("repository") or ""),
            branch=str(values.get("branch") or ""),
            head=str(values.get("head") or ""),
            dirty_paths=values.get("dirty_paths") or [],
            commands=values.get("commands") or [],
            artifacts=values.get("artifacts") or [],
        )
        return _committed(store, frame)
    if action == "status":
        frame = store.status(
            project,
            _actor(values),
            location=str(values.get("location") or os.getcwd()),
            status=str(values.get("status") or "working"),
            artifacts=values.get("artifacts") or [],
            blockers=values.get("blockers") or [],
            next_action=str(values.get("next_action") or ""),
            pct=int(values.get("pct") or 0),
        )
        return _committed(store, frame)
    if action == "handoff":
        frame = store.handoff(
            project,
            from_actor=_actor(values, "from_"),
            to_actor=_actor(values, "to_"),
            document=str(values.get("document") or values.get("doc") or ""),
            open_questions=values.get("open_questions") or [],
        )
        return _committed(store, frame)
    if action == "takeover":
        frame = store.takeover(
            project,
            _actor(values),
            location=str(values.get("location") or os.getcwd()),
            reason=str(values.get("reason") or "expired lease"),
            lease_seconds=int(values.get("lease_seconds") or 3600),
        )
        return _committed(store, frame)
    if action == "punchout":
        frame = store.punchout(
            project,
            _actor(values),
            outcome=str(values.get("outcome") or "done"),
            receipts=values.get("receipts") or [],
            summary=str(values.get("summary") or ""),
        )
        return _committed(store, frame)
    if action == "absorb":
        frame = store.absorb(
            project,
            _actor(values),
            source_uri=str(values.get("source_uri") or ""),
            source_sha256=str(values.get("source_sha256") or ""),
            source_license=str(values.get("source_license") or ""),
            adopted=values.get("adopted") or [],
            rejected=values.get("rejected") or [],
            summary=str(values.get("summary") or ""),
            receipts=values.get("receipts") or [],
        )
        return _committed(store, frame)
    if action == "policy":
        frame = store.set_cell_policy(
            project,
            _actor(values),
            cadence_seconds=int(values.get("cadence_seconds") or 3600),
            may=values.get("may") or [],
            never=values.get("never") or [],
            max_cycles=int(values.get("max_cycles") or 100),
            max_seconds_per_cycle=int(
                values.get("max_seconds_per_cycle") or 900
            ),
            stop_conditions=values.get("stop_conditions") or [],
            human_gates=values.get("human_gates") or [],
        )
        return _committed(store, frame)
    if action == "cycle":
        frame = store.record_cell_cycle(
            project,
            _actor(values),
            observations=values.get("observations") or [],
            proposed=values.get("proposed") or [],
            applied=values.get("applied") or [],
            rejected=values.get("rejected") or [],
            action_classes=values.get("action_classes") or [],
            elapsed_seconds=int(values.get("elapsed_seconds") or 0),
            receipts=values.get("receipts") or [],
        )
        return _committed(store, frame)
    if action == "due":
        return {"status": "ok", "cells": store.due_cells()}
    if action == "approve":
        path = store.approve_model_context(
            project,
            str(values.get("visibility") or "public"),
        )
        return {
            "status": "ok",
            "project": project,
            "approval": str(path),
        }
    if action == "resume":
        return {"status": "ok", **store.resume(project)}
    if action == "verify":
        return {"status": "ok", **store.verify(project)}
    if action == "board":
        return store.board()
    if action == "export":
        path = store.export_egg(project, values.get("path"))
        return {"status": "ok", "project": project, "egg": str(path)}
    if action == "import":
        project = store.import_egg(str(values.get("path") or ""))
        return {"status": "ok", "project": project}
    raise ProjectError(f"unknown action: {action}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="rapp-projects")
    parser.add_argument("action", choices=ACTIONS)
    parser.add_argument("--json", default="{}")
    parser.add_argument("--root")
    args = parser.parse_args(argv)
    try:
        values = json.loads(args.json)
        if not isinstance(values, dict):
            raise ProjectError("--json must be an object")
        root = args.root or os.environ.get("RAPP_PROJECTS_ROOT")
        store = ProjectStore(root) if root else ProjectStore()
        print(json.dumps(dispatch(store, args.action, values), ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "error",
            "action": args.action,
            "message": str(exc),
        }))
        return 1


if __name__ == "__main__":
    sys.exit(main())

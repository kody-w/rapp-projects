"""Portable Brainstem adapter for the public RAPP Projects protocol."""

from __future__ import annotations

import json
import os
import sys

try:
    from agents.basic_agent import BasicAgent
except ImportError:
    try:
        from basic_agent import BasicAgent
    except ImportError:
        class BasicAgent:
            def __init__(self, name=None, metadata=None):
                self.name = name or type(self).__name__
                self.metadata = metadata or {}

from rapp_projects.cli import ACTIONS, dispatch
from rapp_projects.core import ProjectStore


__manifest__ = {
    "schema": "rapp-agent/1.0",
    "name": "@rapp/rapp-projects",
    "version": "0.1.0",
    "display_name": "RAPP Projects",
    "description": (
        "Product-neutral RAPP/1 project hive for punch-in, checkpoints, "
        "handoff, takeover, crash recovery, project eggs, and a global board."
    ),
    "author": "RAPP",
    "tags": ["rapp-1", "projects", "checkpoint", "handoff", "local-first"],
    "category": "productivity",
    "quality_tier": "community",
    "requires_env": [],
    "dependencies": ["rapp-sdk>=0.2.0", "rapp-projects>=0.1.0"],
    "example_call": {"action": "board"},
}


class RappProjectsAgent(BasicAgent):
    def __init__(self):
        self.name = "RappProjects"
        self.metadata = {
            "name": self.name,
            "description": __manifest__["description"],
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": list(ACTIONS)},
                    "project": {"type": "string"},
                    "title": {"type": "string"},
                    "goal": {"type": "string"},
                    "owner": {"type": "string"},
                    "origin": {"type": "string"},
                    "visibility": {
                        "type": "string",
                        "enum": ["local", "team", "public"],
                    },
                    "agent": {"type": "string"},
                    "runtime": {"type": "string"},
                    "session_id": {"type": "string"},
                    "model": {"type": "string"},
                    "host": {"type": "string"},
                    "capabilities": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "location": {"type": "string"},
                    "intent": {"type": "string"},
                    "role": {"type": "string"},
                    "lease_seconds": {"type": "integer"},
                    "status": {"type": "string"},
                    "summary": {"type": "string"},
                    "completed": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "in_progress": {"type": "string"},
                    "next_action": {"type": "string"},
                    "resume_prompt": {"type": "string"},
                    "cwd": {"type": "string"},
                    "repository": {"type": "string"},
                    "branch": {"type": "string"},
                    "head": {"type": "string"},
                    "dirty_paths": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "commands": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "artifacts": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "blockers": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "pct": {"type": "integer"},
                    "from_agent": {"type": "string"},
                    "from_runtime": {"type": "string"},
                    "from_session_id": {"type": "string"},
                    "to_agent": {"type": "string"},
                    "to_runtime": {"type": "string"},
                    "to_session_id": {"type": "string"},
                    "document": {"type": "string"},
                    "open_questions": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "reason": {"type": "string"},
                    "outcome": {
                        "type": "string",
                        "enum": ["done", "blocked", "abandoned"],
                    },
                    "receipts": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "path": {"type": "string"},
                    "source_uri": {"type": "string"},
                    "source_sha256": {"type": "string"},
                    "source_license": {"type": "string"},
                    "adopted": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "rejected": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "cadence_seconds": {"type": "integer"},
                    "may": {"type": "array", "items": {"type": "string"}},
                    "never": {"type": "array", "items": {"type": "string"}},
                    "max_cycles": {"type": "integer"},
                    "max_seconds_per_cycle": {"type": "integer"},
                    "stop_conditions": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "human_gates": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "observations": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "proposed": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "applied": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "action_classes": {
                        "type": "array", "items": {"type": "string"},
                    },
                    "elapsed_seconds": {"type": "integer"},
                },
                "required": ["action"],
            },
        }
        super().__init__(name=self.name, metadata=self.metadata)

    def _store(self) -> ProjectStore:
        root = os.environ.get("RAPP_PROJECTS_ROOT")
        return ProjectStore(root) if root else ProjectStore()

    def system_context(self):
        try:
            configured = os.environ.get(
                "RAPP_PROJECTS_MODEL_VISIBILITY",
                "local,team,public",
            )
            visibilities = tuple(
                value.strip()
                for value in configured.split(",")
                if value.strip() in ("local", "team", "public")
            )
            text = self._store().model_context(visibilities)
            return (
                "<rapp_projects>\n"
                + text[:7000]
                + "\n</rapp_projects>"
            )
        except Exception as exc:
            return (
                "<rapp_projects_alert>"
                + str(exc)[:500]
                + "</rapp_projects_alert>"
            )

    def perform(self, **kwargs):
        action = str(kwargs.get("action") or "board")
        try:
            return json.dumps(
                dispatch(self._store(), action, dict(kwargs)),
                ensure_ascii=False,
            )
        except Exception as exc:
            return json.dumps({
                "status": "error",
                "action": action,
                "message": str(exc),
            })


if __name__ == "__main__":
    print(RappProjectsAgent().perform(action="board"))

# RAPP Projects interoperability

RAPP Projects is product-neutral. Any runtime that can call a CLI or read/write
the protocol may participate.

## Actor envelope

```json
{
  "id": "claude-code",
  "runtime": "claude-code",
  "session_id": "runtime-session-id",
  "model": "optional-model",
  "host": "optional-host",
  "capabilities": ["files", "shell", "tests"]
}
```

No vendor or model is privileged. `id` and `runtime` are declarations recorded
for audit; authorization belongs to the host environment.

Each runtime may contribute through `cell.absorb`, but the receiving project
records exactly what it adopted and rejected. RAPP Cell never means silently
copying another product or erasing provenance.

Autopilot is also runtime-neutral. `rapp-projects due` returns due project eggs
and policies. Any scheduler may wake a compatible runtime, which records one
`cell.cycle`. Hidden, unbounded daemon behavior is not protocol-compliant.

## Universal adapter

The stable command is:

```text
rapp-projects <action> --json <object>
```

The output is one JSON object. Exit code `0` means the action committed; nonzero
means no success should be inferred.

## Runtime examples

- GitHub Copilot CLI: call the command through its shell tool.
- Claude Code: call the same command through Bash.
- Hermes or Grok agents: execute the CLI or implement the same JSON envelope.
- RAPP Brainstem: install `agents/rapp_projects_agent.py` and use `/chat`.
- CI: checkpoint before a destructive stage and punch out with build artifacts.

## Resume sequence

1. Read `CATCHUP.md`.
2. Read the selected project's `docs/RESUME.md`.
3. Verify or import `PROJECT.egg`.
4. If the prior lease is active, request handoff.
5. If it expired because the device or runtime disappeared, append
   `work.takeover`.
6. Continue from the exact checkpoint and publish a new status frame.

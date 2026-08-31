# RAPP Projects release plan

## Product

RAPP Projects is a public, product-neutral collaboration protocol built on
RAPP/1. It gives Copilot CLI, Claude Code, Hermes, Grok, local models, cloud
agents, CI workers, and humans one durable project memory.

The global RAPP Brainstem is one possible project manager, not a protocol
dependency.

## Applications

1. **Core store** — atomic RAPP/1 frame journal, derived board, checkpoints,
   leases, takeover, recovery, and portable project eggs.
2. **CLI** — the universal adapter for any runtime that can execute a command.
3. **Brainstem agent** — a portable `*_agent.py` adapter exposing the same
   actions through `/chat`.
4. **RAPP SDK integration** — typed project frame, actor, checkpoint, stream,
   and project-egg helpers in `rapp-sdk`.

The adaptation story is **RAPP Cell**: every project is a mutating RAPP/1 egg
that can absorb verified capabilities and lessons without creating a new wire
type.

## Protocol events

All events are carried by the registered `body.pulse` RAPP/1 frame kind.

- `project.genesis`
- `work.punchin`
- `work.heartbeat`
- `work.checkpoint`
- `work.status`
- `work.handoff`
- `work.takeover`
- `work.punchout`
- `cell.policy`
- `cell.cycle`
- `cell.absorb`
- `project.verify`

## Storage contract

```text
~/.rapp/projects-control/
  PROTOCOL.md
  INTEROP.md
  BOARD.md
  CATCHUP.md
  index.json
  projects/<slug>/
    rappid.json
    frames/00000000000000000000-<frame_hash>.json
    chain.jsonl                 # derived projection
    docs/STATUS.md
    docs/HANDOFF.md
    docs/RESUME.md
    docs/notes/*.md
    PROJECT.egg                # derived portable snapshot
```

Individual `body.pulse` frame files are authoritative and committed by write + fsync +
atomic rename + directory fsync. Markdown, JSONL, indexes, and eggs are
rebuildable projections.

## Roomba / hard-power-loss acceptance

1. A crash before atomic rename exposes no frame.
2. A crash after frame rename but before projection writes keeps the frame.
3. Restart reconstructs `chain.jsonl`, Markdown, index, and `PROJECT.egg`.
4. A partial or corrupt projection never damages authoritative frames.
5. The latest checkpoint preserves exact runtime, session, worktree, branch,
   commit, dirty paths, completed work, in-progress work, commands, artifacts,
   blocker, next action, and a ready-to-paste resume prompt.
6. An expired lease permits a declared `work.takeover`; an active lease does
   not.
7. An autopilot cell cannot run without a policy, cannot exceed its cycle
   budget, and cannot place irreversible actions in its autonomous `may` set.
8. Every `PROJECT.egg` verifies as the registered RAPP/1 `organism` variant;
   no project-specific egg schema or ZIP profile is emitted.

## Release gates

- Unit tests for every frame and payload rule.
- Concurrent writers retain one contiguous chain.
- Tampering and divergent egg imports fail closed.
- Cross-runtime handoff and takeover preserve exact resume state.
- CLI and Brainstem adapter use the same core.
- Public repository contains no private paths, credentials, customer data, or
  RapterBox-specific behavior.
- SDK and reference app pass their complete existing and new suites.
- Public GitHub repositories are pushed only after all gates are green.

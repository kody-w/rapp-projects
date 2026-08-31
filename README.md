# RAPP Projects

> A shared, crash-safe project memory for Copilot CLI, Claude Code, Hermes,
> Grok, local models, cloud agents, CI workers, and humans.

RAPP Projects is a public protocol and reference implementation built on
RAPP/1. It replaces transcript archaeology with an append-only project record:
who is working, where, what changed, what is blocked, what comes next, and the
exact prompt needed to resume after a crash.

## The problem

An AI works for an hour. The laptop loses power. A different AI opens tomorrow.
Without a durable protocol, the new runtime must reconstruct the project from
chat history, shell history, dirty files, and memory.

RAPP Projects makes the handoff a verified artifact.

## RAPP Cell

Every project is a **RAPP Cell**: a normal RAPP/1 `organism` `.egg` that mutates
through registered `body.pulse` frames and can absorb verified lessons or
capabilities from other agents. “Cell” is the story and adaptation pattern,
not a new data type.

```bash
rapp-projects absorb --json '{
  "project":"example",
  "agent":"github-copilot-cli",
  "runtime":"copilot-cli",
  "session_id":"session-1",
  "source_uri":"https://github.com/example/useful-agent",
  "source_sha256":"0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "source_license":"MIT",
  "adopted":["retry strategy","checkpoint format"],
  "rejected":["automatic external sending"],
  "summary":"Absorbed the safe retry and checkpoint patterns.",
  "receipts":[]
}'
```

`cell.absorb` preserves provenance, license, adopted parts, rejected parts, and
receipts. The cell learns without pretending it invented the source.

### Bounded autopilot

A cell grows on its own only after a `cell.policy` declares cadence, allowed
work, forbidden work, budgets, stop conditions, and human gates.

```bash
rapp-projects policy --json '{
  "project":"example",
  "agent":"global-brainstem",
  "runtime":"rapp-brainstem",
  "session_id":"pm-1",
  "cadence_seconds":3600,
  "may":["read","test","draft","write_local"],
  "never":["send","sign","pay","purchase","delete_external","publish_remote"],
  "max_cycles":100,
  "max_seconds_per_cycle":900,
  "stop_conditions":["goal complete","receipt verification fails"],
  "human_gates":["external side effect","budget increase"]
}'

rapp-projects due --json '{}'
```

The scheduler decides which due cell to wake. The selected runtime reads its
`PROJECT.egg` and `RESUME.md`, performs one bounded cycle, and records a
`cell.cycle` frame. Different cells may grow differently without sharing
mutable hidden state.

Each cycle declares `action_classes` and `elapsed_seconds`. The reference store
rejects classes outside `may`, classes inside `never`, time overruns, and cycle
budget overruns.

## What survives a hard power loss

- atomic RAPP/1 frame files;
- current actor, runtime, model, session, lease, location and intent;
- completed and in-progress work;
- branch, commit and dirty paths;
- commands already run;
- content-addressed artifact receipts;
- blockers and next action;
- a ready-to-paste resume prompt;
- a continuously rebuilt `PROJECT.egg`.

A frame committed before power loss survives. Markdown, JSONL, indexes, and
eggs are reconstructed from authoritative frames on restart.

## Quickstart

```bash
git clone https://github.com/kody-w/rapp-projects
cd rapp-projects
./install.sh

rapp-projects open --json '{
  "project":"example",
  "title":"Example",
  "goal":"Ship without losing context",
  "owner":"me",
  "origin":"local"
}'

rapp-projects punchin --json '{
  "project":"example",
  "agent":"github-copilot-cli",
  "runtime":"copilot-cli",
  "session_id":"session-1",
  "capabilities":["files","shell","tests"],
  "location":"/absolute/worktree",
  "intent":"implement the store",
  "role":"builder"
}'
```

Before risky work or whenever the project phase changes:

```bash
rapp-projects checkpoint --json '{
  "project":"example",
  "agent":"github-copilot-cli",
  "runtime":"copilot-cli",
  "session_id":"session-1",
  "summary":"Core is implemented; import remains",
  "completed":["atomic frame journal","board projection"],
  "in_progress":"project egg import",
  "next_action":"make divergent imports fail closed",
  "resume_prompt":"Open tests/test_egg.py and continue the divergence case.",
  "cwd":"/absolute/worktree",
  "repository":"https://github.com/example/project",
  "branch":"feature/import",
  "head":"0123456789abcdef0123456789abcdef01234567",
  "dirty_paths":["src/rapp_projects/core.py"],
  "commands":["python -m pytest tests/test_egg.py"],
  "artifacts":[]
}'
```

If Claude Code takes over:

```bash
rapp-projects takeover --json '{
  "project":"example",
  "agent":"claude-code",
  "runtime":"claude-code",
  "session_id":"claude-session",
  "capabilities":["files","shell","tests"],
  "location":"/absolute/worktree",
  "reason":"The prior runtime lease expired after power loss."
}'

rapp-projects resume --json '{"project":"example"}'
```

## One central place

Default root:

```text
~/.rapp/projects-control/
```

Read:

- `BOARD.md` — every project at a glance;
- `CATCHUP.md` — where to resume after interruption;
- `projects/<slug>/docs/RESUME.md` — exact checkpoint;
- `projects/<slug>/PROJECT.egg` — portable verified project snapshot.

## Brainstem

`install.sh` copies `agents/rapp_projects_agent.py` into the local Brainstem.
Agents are hot-loaded; no restart is required. The adapter injects the current
approved project summary into Brainstem context and exposes the same protocol
actions through `POST /chat`.

Imported or newly created projects are **not** model-visible merely because
their own frame says `public`. The owner must approve the matching visibility
locally:

```bash
rapp-projects approve --json '{
  "project":"example",
  "visibility":"public"
}'
```

## Protocol and SDK

- [`PROTOCOL.md`](PROTOCOL.md) — frame and storage contract
- [`INTEROP.md`](INTEROP.md) — product-neutral runtime adapter contract
- [`PLAN.md`](PLAN.md) — acceptance plan and failure gates
- [`rapp-sdk`](https://github.com/kody-w/rapp-sdk) — typed Python primitives

## Safety

- GODD stays local by default.
- Project eggs exclude artifact bodies; frames carry paths and hashes.
- Divergent histories are refused, never silently merged.
- No project frame authorizes send, sign, pay, delete, or publish.
- Derived views never override the verified frame record.

## Tests

```bash
python -m pytest -q
```

The suite includes concurrent writers, tampering, cross-runtime takeover,
project-egg divergence, and simulated crashes before and after atomic frame
commit.

## License

MIT.

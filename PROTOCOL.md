# RAPP Projects protocol

## Status

Version `rapp-projects/1`, built on `rapp/1`.

## Project events

Every row below is a project event in the payload of the already registered
RAPP/1 `body.pulse` frame kind.

| Event | Required purpose |
|---|---|
| `project.genesis` | Establish project identity, goal, owner, origin and visibility. |
| `work.punchin` | Declare actor, runtime, session, location, role, intent and lease. |
| `work.heartbeat` | Renew a lease and publish liveness. |
| `work.checkpoint` | Persist exact resume state before interruption or risky work. |
| `work.status` | Publish progress, artifacts, blockers and next action. |
| `work.handoff` | Transfer responsibility with a central Markdown handoff. |
| `work.takeover` | Continue after an expired lease or lost runtime. |
| `work.punchout` | Stop as done, blocked or abandoned with receipts. |
| `cell.policy` | Declare cadence, autonomy envelope, budgets, stop conditions and human gates. |
| `cell.cycle` | Record one bounded autonomous observe/propose/apply/reject cycle. |
| `cell.absorb` | Adopt verified parts of another capability with provenance and explicit rejection. |
| `project.verify` | Record frame and receipt verification. |

All are RAPP/1 body frames. Their payloads are application-level vocabulary;
the eleven-key RAPP/1 frame, canonical bytes, hashes, sequence, previous
payload link and trust boundary remain unchanged.

## Atomic authority

The authoritative journal is one atomically renamed file per frame:

```text
frames/<20-digit-seq>-<frame-hash>.json
```

Commit order:

1. build and verify the complete frame;
2. write a unique temporary file;
3. flush and fsync the file;
4. atomically rename to the final frame filename;
5. fsync the frames directory;
6. rebuild projections.

A crash before step 4 commits nothing. A crash after step 4 commits the frame,
even if every projection is missing.

## Checkpoint

`work.checkpoint` records:

- actor/runtime/model/session/capabilities;
- summary, completed work, in-progress work and next action;
- exact resume prompt;
- cwd, repository, branch, HEAD and dirty paths;
- commands already run;
- artifact paths and content hashes.

## Lease and takeover

`work.punchin` and `work.heartbeat` declare `lease_expires_utc`.
`work.takeover` is refused while the lease is active unless an explicit
`work.handoff` transferred responsibility. An expired lease may be taken over
with a reason and the prior lease frame hash.

## Project egg

`PROJECT.egg` is a normative `rapp/1-egg` using the registered `organism`
variant. It has the exact seven-member manifest, `Hb("rapp/1:egg", file_octets)`
content hashes, canonical manifest bytes, stored ZIP entries, deterministic
ordering/timestamps, root `rappid.json` and `soul.md`, authoritative frames,
protocol documents, and resume Markdown. Artifact bodies are excluded. Import
verifies every entry and every frame. Divergent local and incoming chains are
refused.

## Visibility

- `local` — do not distribute without explicit owner approval;
- `team` — intended for a declared team boundary;
- `public` — safe to publish after an independent content review.

Visibility does not weaken integrity checks.
Visibility is also not self-authorizing: automatic model context requires a
separate local approval outside the imported project egg.

## RAPP Cell

A project is a **RAPP Cell**: its standard organism `.egg` is the membrane, its RAPP/1 frames are
the mutation record, and `cell.absorb` is the controlled adaptation operation.
This does not introduce a new protocol type. It remains registered
`body.pulse` frames inside a `rapp/1-egg`.

Absorption requires source URI, source hash, license, adopted parts, rejected
parts, summary, actor, and receipts. Copying behavior without provenance is not
absorption and must not be recorded as one.

### Autopilot

`cell.policy` is required before `cell.cycle`. The reference implementation
refuses irreversible action classes in `may`, requires them in `never`, enforces
positive cycle/time budgets, checks every cycle's declared action classes and
elapsed time, and stops when the cycle budget is exhausted.
The scheduler wakes cells whose `next_wakeup_utc` is due; the protocol does not
privilege a scheduler vendor.

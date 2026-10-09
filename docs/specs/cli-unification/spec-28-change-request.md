# DRAFT change request to spec 28: the CLI mode grammar

**Status: DRAFT. Not accepted, and it changes nothing yet.** This document is a proposal. Spec
28 (`specs/28_BOOTSTRAP_INIT_CLIENT.md`) and the frozen command table stay authoritative until
the change is accepted through review. Acceptance needs a reviewed edit to spec 28 and the
traceability listed in §8. The gaps are recorded in `OPEN_GATES.md` under "CLI mode grammar
(spec 28 change request)".

Source: [`design.md`](design.md) §9 (the change request it names), and the change-request draft
in Task 4, Step 1 of the implementation plan (`InferWeave/inferweave` branch
`feat/cli-unification`, `docs/superpowers/plans/2026-10-07-cli-unification.md`). That draft reads:

> (a) Add the mode table and placement rules […] as the addressable contract beside the frozen
> command table; every frozen spelling stays an alias without a warning.
> (b) The relay commands (`inferweave relay init|join|run|healthcheck`) and the cluster commands
> join the JSON envelope and the exit-code table (the cluster commands keep their documented
> `128+signal` exits).
> (c) The standard flags `--json`, `--config-dir`, `--state-dir`, `--yes`, `--help`, `--version`.

This document expands those three points into contract text and adds the compatibility
obligations. Where the plan's rulings corrected the design (its "Spec defects found" table, D1
to D13), the corrected form is used here, and the defect is named.

## 1. Where the frozen contract lives today

The contract is split across two repositories. Spec 28 does not contain all of it:

- **Spec 28** fixes one binary (`inferweave`), `--json` on every discovery/planning/health command,
  "versioned machine-readable schemas and stable exit codes", the role list, and the command
  names. The "Core commands" block lists 13 spellings. `init plan <role>` and `init <role>` are one
  command, so that is 12 distinct commands. `config export` and `support-bundle` appear in later
  sections, which makes the 14 frozen commands: `doctor`, `probe`,
  `init`, `enroll`, `verify`, `status`, `logs`, `update`, `backup`, `restore`, `uninstall`, `mcp`,
  `config`, `support-bundle`.
- **Spec 28 has no envelope definition and no exit-code table.** The four-row exit table
  (`0` ok, `1` internal_error, `2` usage_error, `3` not_implemented), the envelope
  (`schemaVersion`, `command`, `status`, `data`, `error`), the closed status and error-code
  vocabularies and the usage messages were frozen by task `P0-T03` (`IW-BOOT-001`, `IW-BOOT-004`).
  They live in the implementation repository: `docs/specs/cli.md` ("Commands", "Envelope",
  "Status and error codes", "Exit codes") and `schemas/json-schema/cli_*.json`.

In this document, "the frozen table" means that combined contract. This change request
**proposes** that spec 28 carry, or normatively reference, the envelope and the exit-code
table, so that the relay rows in §3 have a canonical place. It does not edit them.

## 2. (a) The mode table and placement rules become the addressable contract

### 2.1 Grammar

`inferweave <mode> <command> [options]`. Mode and command are lowercase ASCII. A hyphen is used
only when a word cannot be avoided. The modes are fixed: `node`, `gateway`, `relay`, `cluster`,
`bench`, `system`, `dev`. A new mode needs a spec change. A new command must pick a mode.

Every spelling the frozen table names stays an **alias** of its mode spelling, permanently while
spec 28 stands, and **without a warning**. Example: `inferweave doctor` is
`inferweave system doctor`.

### 2.2 Placement rules (design §3.1)

1. A command lives under the mode whose thing it acts on, not the mode that happens to ship it.
2. A noun that already has a mode is never also a top-level command (`cluster-capability` becomes
   `cluster capability`).
3. `inferweave system …` acts on the installation as a whole. Per-role actions go under the
   role's mode: `gateway status` reports the gateway, `system status` the installation.
4. The modes are fixed in the command table (above).

Standard verbs: `init`, `run`, `status`, `doctor`, `update`, `uninstall`, `logs`. A command with
one of those meanings uses that verb. The one documented exception is `gateway serve`, because
`run` would clash with `node run`.

### 2.3 The mode table

This table is the design's §3, corrected by the plan's rulings (D1, D2, D5, D12). "Replaces"
gives the spelling it aliases. `—` means the row is new.

| Mode | Command | Replaces |
|---|---|---|
| `node` | `join` | `inferweave join` |
| `node` | `run` | `inferweave node-run` |
| `node` | `gpu` | `inferweave gpu-residency` |
| `node` | `pick-config` | `inferweave pick-config` |
| `node` | `init` | `inferweave init node` |
| `node` | `proxy` | `inferweave-node-proxy` |
| `node` | `watchdog` | `inferweave-node-watchdog` |
| `node` | `runtime` | `adaptive-runtime` (production helper, so not `dev`: D2) |
| `node` | `runtime-service` | `adaptive-runtime-service` (its own row: D2) |
| `gateway` | `serve` | `inferweave-gateway` |
| `gateway` | `init` | `inferweave init gateway` |
| `gateway` | `enroll` | `inferweave enroll create` |
| `gateway` | `drain` | `inferweave-drain` |
| `gateway` | `status` | — (not implemented: exit `3`) |
| `relay` | `init` | `iw-relay init` |
| `relay` | `join` | `iw-relay join` |
| `relay` | `run` | `iw-relay run` |
| `relay` | `healthcheck` | `iw-relay healthcheck` |
| `relay` | `console` | — (not implemented: exit `3`; D12) |
| `relay` | `status` | — (not implemented: exit `3`) |
| `cluster` | `init` | `inferweave cluster init` |
| `cluster` | `tunnel` | `inferweave cluster tunnel` |
| `cluster` | `ensure` | `inferweave cluster ensure` |
| `cluster` | `capability` | `inferweave cluster-capability` |
| `cluster` | `recommend` | `inferweave recommend-placement` |
| `bench` | `run` | `inferweave-bench` |
| `bench` | `sweep` | `benchmark-sweep` |
| `bench` | `adaptive` | `benchmark-adaptive` |
| `bench` | `eval` | `inferweave-eval` |
| `bench` | `profile` | `inferweave profile` |
| `system` | `doctor`, `probe`, `verify`, `status`, `logs`, `update`, `backup`, `restore`, `uninstall`, `support-bundle`, `config`, `mcp` | the same frozen name at top level |
| `system` | `init` | `inferweave init <edge\|site\|proxy\|slurm-worker\|dev>` and `init plan <role>` (D1) |
| `system` | `completions` | — (`system completions bash`) |
| `dev` | `mock` | `inferweave-devmock` |
| `dev` | `schema` | `schema-gen` |
| `dev` | `node-ui` | `node-ui-preview` |

`init` mapping (D1): `init gateway` → `gateway init`, `init node` → `node init`,
`init <edge|site|proxy|slurm-worker|dev>` → `system init <role>`,
`init plan <role>` → `system init plan <role>`. `system init gateway` and `system init node` are
usage errors that name the role's own mode. `enroll create` → `gateway enroll`.

Not in any mode (D5): `adaptive-sim` and `conformance` are test-harness executables.

The command table is the single source. Help, completions and the documentation render from it,
and a test fails when code and table disagree.

## 3. (b) The relay and cluster commands in the envelope and the exit-code table

### 3.1 `inferweave relay`

Today `iw-relay` is a separate executable outside the envelope and outside the exit-code table
(implementation `docs/specs/cli.md`, "`iw-relay`": "does not follow the `inferweave` envelope or
the spec-28 exit-code table"). Proposed:

- `inferweave relay <init|join|run|healthcheck> --json` writes exactly one envelope on stdout:
  `command` `"relay"`, `data.subcommand` the relay command, and the usual `schemaVersion`,
  `status`, `data` and `error`. This follows `cluster`'s precedent of one `command` value for
  the mode. Human output goes to stderr. `relay run --json` logs to stderr.
- Exit codes map onto the existing four rows. No row is added:

  | Relay exit | Meaning today | Envelope `status` / `error.code` | Exit |
  |---|---|---|---|
  | `0` | success | `ok` | `0` |
  | `1` | a failed step (missing `ssh-keygen`, untrusted host key, unwritable file, an endpoint that did not answer 2xx for `healthcheck`) | `error` / `internal_error` | `1` |
  | `2` | an invalid argument (bad join string, missing identity file, non-loopback `--listen`, `--proxy-jump` without `--ssh-config-host`, explicit `--config-dir` without `relay-ssh.json`) | `error` / `usage_error` | `2` |
  | — | `relay console`, `relay status` (not implemented) | `not_implemented` / `not_implemented` | `3` |

  Disclosure: the frozen meaning of `internal_error` is "unexpected failure inside the CLI". A
  relay exit `1` is often an *expected* failed step, such as an untrusted host key. Mapping it to
  `internal_error` keeps the four-row table unchanged, but it widens what that row means in
  practice. The same is already true of `cluster` (every `cluster` failure is exit `1`
  and `internal_error`, with the stable name in `data.error`). Reviewers should accept this
  explicitly or ask for a closed `data.error` vocabulary for the relay, as `cluster` has.
- A parser error under `--json` is the stable envelope message
  ``relay: unknown argument; run `inferweave relay --help` `` (exit `2`). The parser's own text
  stays on stderr.
- `inferweave relay` with no command is a usage error (exit `2`) that lists the relay commands.
  Only the old `iw-relay` executable defaults to `run`.

### 3.2 `inferweave cluster`

`cluster` already answers inside the envelope (design defect D4: the design said it was outside),
so (b) only makes that canonical. The `128 + signal` exits of `cluster tunnel` and `cluster init`
(`130` after SIGINT, `143` after SIGTERM) stay documented **beside** the four-row table, not as
rows in it, exactly as today.

### 3.3 The envelope's `command` field

Until this change request is accepted, a rewritten command keeps its legacy wire name. For
example, `inferweave system doctor --json` says `"command":"doctor"`. The relay says
`"relay"`, as above. A row that is only planned answers `"command":"<mode> <command>"`.
`schemas/json-schema/cli_envelope.json` types `command` as a free string, not an enum, so no
schema change is needed. The crate's frozen `ALL_COMMANDS` stays the 14 names. `relay`, like
`cluster`, is a `command` value outside it.

## 4. (c) The standard flags

Spelled the same in every mode where they have a meaning:

| Flag | Meaning |
|---|---|
| `--json` | One envelope on stdout (envelope commands only, see below) |
| `--config-dir DIR` | The configuration directory |
| `--state-dir DIR` | The state directory |
| `--yes` | Proceed without the interactive confirmation |
| `--help` | Help for the mode or command (stdout, exit `0`) |
| `--version` | Version |

- Secrets are never flag values. They are `--<name>-file` paths or environment variables
  (existing rule, kept).
- `--json` is the standard flag of **envelope** commands. Process-owning commands keep their own
  output contract: `gateway serve`, `gateway drain`, `node proxy|watchdog|runtime|runtime-service`,
  `bench run|sweep|adaptive|eval` and `dev *`. This CR does not put them in the envelope.
- No tool today spells a directory flag two ways (design defect D6). There is no `--dir`, and
  `--config` names a file, which is a different idea. So no old flag spelling is deprecated by
  this change. The rule binds new commands.
- `inferweave help [mode [command]]` and `inferweave <mode> [command] --help` print the same text.

## 5. What does not change (the 14 frozen commands)

For every argv the frozen table names, stdout, the envelope and the exit code stay exactly as
they are:

- the 14 commands, their fixed shapes (`init <role>`, `init plan <role>`,
  `enroll create --role <role>`, `config export`), the role list, and the frozen doctor check list
  (`ALL_DOCTOR_CHECKS`, `doctor_check.json`);
- the envelope shape and `schemaVersion`, the closed `status` and `error.code` vocabularies, and
  the redaction rule with `--reveal-secrets`;
- the four exit codes `0/1/2/3` and their meanings;
- the usage messages `unknown command: <x>` and `no command given; try 'inferweave --help'`;
- the frozen 14 never print a deprecation line.

What does change are answers to argv the frozen table never named, all of which are usage errors
(exit `2`) today:

- `inferweave help [...]` exits `0` (today: `unknown command: help`, exit `2`);
- the mode words `node`, `gateway`, `relay`, `bench`, `system`, `dev`, and `cluster capability|recommend`, are
  now commands;
- `inferweave cluster <sub> --help` prints help, exit `0` (implementation defect D11: `cli.md`
  documented exit `2`);
- `inferweave --help` gains a MODES section before ROLES. The COMMANDS listing and every other
  line stay the same.

Unknown top-level word (D9): the envelope message stays the frozen `unknown command: X`, and the
nearest names go to **stderr** only. Inside a mode, the message names the mode, the nearest
commands and "run `inferweave help <mode>`".

A check for artifacts that still name old executables is `inferweave system doctor --artifacts`
(envelope command `doctor-artifacts`). It is **not** a tenth doctor check, so the frozen check
list is untouched (D3). Legacy `doctor --artifacts` stays a usage error.

## 6. Compatibility obligations

1. **Shims.** Every old executable name keeps working for at least two minor releases after the
   mode spelling ships. Each calls the same library function as the mode spelling in-process.
   Removing a shim is a separate, later decision and is not part of this change.
2. **Deprecation line on stderr only.** A deprecated spelling prints exactly one line to stderr,
   before anything else: `<old spelling> is deprecated; use: inferweave <mode> <command>`. It never
   writes the line to stdout. Its stdout and exit code equal the mode spelling's byte for byte.
   Under `--json` the envelope is unchanged. A launcher that captures
   `$(inferweave pick-config --emit runtime …)` must see the same bytes.
3. **Who warns.** The frozen 14 never warn. The seven non-frozen top-level commands warn: `join`,
   `pick-config`, `gpu-residency`, `node-run`, `profile`, `recommend-placement` and
   `cluster-capability`. Every old executable warns. `cluster …` is spelled the same in both
   grammars and does not warn.
4. **One known difference (D7).** `iw-relay … --json` stays what it is today, a parser error with
   exit `2`. Only `inferweave relay … --json` answers an envelope. An old executable's own `--help`
   and `--version` are unchanged. So "byte for byte" is measured against the old executable's own
   behaviour for these flags, not against the new spelling.
5. **Artifacts keep working.** Files written by an older spelling (sbatch script and
   `gateway.json` from `cluster init`, the join string's `ensure_program`, the relay's systemd or
   launchd unit) keep naming the executable that wrote them, and they keep working through the
   shims. New installs write the spelling that ran: `inferweave relay join` installs a unit that
   runs `<inferweave> relay run --config-dir D`, and `iw-relay join` keeps writing `<iw-relay> run …`.
6. **Builds without a mode.** A mode not compiled into the build answers
   `this build has no <mode> mode; install the full build` (exit `2`, one envelope under `--json`),
   and is never reported as unknown. `cluster init` on a build without the gateway mode must not
   write `gateway serve` through itself into `gateway.json` (D8).

## 7. Relationship to decisions

- `D-013` (one Rust `inferweave` CLI is the canonical install/init interface): this change is
  consistent with it and moves the relay commands under that one CLI. The separate `iw-relay`
  executable is in tension with `D-013` today. The change does not amend `D-013`.
- `D-001`, `D-002`: not affected.
- This change does not alter a resolved decision, so it does not need an ADR. If review decides
  that changing the addressable contract of spec 28 is architectural, an ADR becomes a condition of
  acceptance.

## 8. What acceptance requires (none of it done in this draft)

- A reviewed edit to `specs/28_BOOTSTRAP_INIT_CLIENT.md`: the mode grammar and table (§2),
  the envelope and exit-code table carried or referenced normatively, with the relay mapping
  (§3), the standard flags (§4), and the compatibility obligations (§6).
- Feature IDs. None is assigned here. Whether this work extends `IW-BOOT-001`/`IW-BOOT-004` or
  needs a new ID is for the operator to approve. Inventing one in a draft would be traceability
  nobody has approved.
- `contracts/feature-registry.json`, `contracts/canonical-task-graph.json`,
  `implementation/CANONICAL_IMPLEMENTATION_SEQUENCE.md`, task cards and coverage files, once an ID
  exists.
- Proof. Every test in design §8 (table parse and drift, shim stdout and exit equality,
  deprecation on stderr only, relay-only build contents, standard flags, unchanged spec-28
  conformance, static musl relay-only build) is `owed` for this repository. None has been run
  against an accepted contract.
- Independent review. The independent review gate in `OPEN_GATES.md` is BLOCKED, and this draft has
  not been reviewed by anyone other than its author.

Still open from the plan, not settled here:

- **D10.** The default build (all modes but `dev`) would link PostgreSQL and SQLite into the static
  compute-node `inferweave`. The node release is therefore built without the gateway mode, and hive's
  gateway-side scripts cannot move to `inferweave gateway …` until someone decides whether the node
  release may carry the gateway mode.
- **D13.** The `adaptive-runtime` and `adaptive-runtime-service` shims cannot be removed until their
  callers (`runtime_program`, `--runtime`) accept an argv rather than a single executable path.

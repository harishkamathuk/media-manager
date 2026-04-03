# media-manager

`media-manager` is a deterministic, failure-sensitive media management engine for planning and applying file organization work with durable state boundaries. It is built around explicit `plan` and `apply` phases so that planning stays side-effect free, while filesystem mutation happens only after durable database gating.

The project is designed for restart safety, idempotent operations, and operator visibility. It is built around a FastAPI-backed application service, an HTTP-first operator console, structured documentation, and observability hooks for production-style workflows.

Status: early-stage and still evolving toward a broader public release. Expect active changes in workflows, operator UX, and documentation while the core safety model remains the anchor.

## Key capabilities

- Deterministic planning that produces reproducible planned actions for identical inputs.
- Restart-safe apply execution with explicit durable state transitions.
- Canonical persistence and policy-driven canonicalization workflows.
- Drift detection, structured failure recording, and operator-focused observability.
- HTTP-first operation model for the operator console, admin tooling, and automation clients.
- Performance and Prometheus metrics support for planner, apply, ingest, and cache behavior.

## Why this project is different

This repository is not a generic scripting playground or a thin file-moving utility. The core operating model is built around runtime invariants:

- No filesystem mutation without durable DB gating.
- Planning has zero side effects.
- Apply consumes durable planned state instead of inventing work on the fly.
- Operations are designed to be idempotent and restart-safe.
- Failures and drift must become durable, observable facts.

Those rules are enforced throughout the system design and are documented in [AGENTS.md](AGENTS.md), [Architecture Invariants](documentation/architecture/invariants.md), and the [Run Lifecycle docs](documentation/architecture/run-lifecycle.md).

## Architecture at a glance

- Planner: reads durable state and emits deterministic `planned_actions`.
- Apply Engine: consumes planned actions and performs filesystem mutation only after DB gating.
- Canonical Persistence Layer: stores content, instances, policies, and run state durably.
- Drift Detection: makes divergence visible instead of silently masking it.
- Failure Logging: records failure events as durable facts.
- Run Lifecycle Controller: defines explicit state boundaries for crash recovery and resume safety.

Deeper architecture material lives in [documentation/architecture/](documentation/architecture/index.md) and [documentation/STATE_MACHINE.md](documentation/STATE_MACHINE.md).

## Interfaces

### HTTP API

The REST API is the only supported application interface. The FastAPI app exposes service-layer endpoints under `/api/*` for status, runs, policy, plan/apply triggers, audit operations, and administrative workflows. Metrics are exposed at `/metrics` for Prometheus scraping, while the Admin UI consumes curated observability endpoints under `/api/admin/observability/*`.

See [API Documentation](documentation/api/index.md) for the module-oriented reference and the [API-only transition notes](documentation/architecture/api-only-transition.md) for migration details.

### Operator Console

The operator console is served by FastAPI and includes a React v2 shell for the Home, Import, Organize, Library, Duplicate Review, and Admin flows. It is an HTTP client of the `/api/*` service surface, intended for operational visibility and controlled execution rather than replacing the system safety model.

Relevant docs:

- [Operator Console API](documentation/api/api-operator-console.md)
- [Operator Guide](documentation/operator-guide/index.md)
- [GUI integration notes](operator_console/gui_app/README.md)

## Quick start

### Prerequisites

- Python 3.11+
- PostgreSQL
- Git

### Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[docs]"
```

### Configure the environment

Use the committed example template to create a local-only runtime file:

```bash
cp .env.sample .env
```

Set at least:

```bash
DATABASE_URL='postgresql+psycopg://user:password@localhost:5432/media_manager'
TEST_DATABASE_URL='postgresql+psycopg://user:password@localhost:5432/media_manager_test'
```

`DATABASE_URL` is required for runtime operation. Full variable reference: [documentation/reference/environment-variables.md](documentation/reference/environment-variables.md).

Keep `.env` local to your machine. It is ignored by Git and should not be committed.

### Initialize the database schema

Before running Alembic, ensure the PostgreSQL database referenced by `DATABASE_URL` exists. Create it if needed:

```bash
createdb media_manager_db
```

Verify that `DATABASE_URL` in `.env` is correct and points to an accessible PostgreSQL instance. Then apply the Alembic migrations:

```bash
alembic upgrade head
```

### Start the API service

Use the packaged API launcher:

```bash
media-manager-api
```

Or run Uvicorn directly:

```bash
uvicorn operator_console.main:app --reload
```

The console also exposes `/metrics` for Prometheus. To force the React v2 shell on the main console routes, set `MEDIA_MANAGER_UI_V2_ENABLED=true`. The v2 shell is also available directly at `/console-v2`.

To enable the new observability links and benchmark queueing in the Admin UI, configure:

```bash
MEDIA_MANAGER_METRICS_ENABLED=true
MEDIA_MANAGER_PROMETHEUS_URL=http://127.0.0.1:9090
MEDIA_MANAGER_GRAFANA_URL=http://127.0.0.1:3000
MEDIA_MANAGER_BENCHMARKS_ENABLED=true
MEDIA_MANAGER_BENCHMARK_STALE_AFTER_SECONDS=900
```

Then start the benchmark worker in a separate process when benchmarking is needed:

```bash
media-manager-benchmark-worker
```

### Run a first plan/apply cycle

Choose a file or directory containing media files, then call the API:

```bash
curl -X POST http://127.0.0.1:8000/api/plan \
  -H 'Content-Type: application/json' \
  -d '{"folder_path":"/path/to/media","strict_metadata":false}'
```

The response includes a durable `run_id` inside `data.result.run_id`.

Apply the planned run:

```bash
curl -X POST http://127.0.0.1:8000/api/apply \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"<RUN_ID>","collision_mode":"rename"}'
```

`apply` consumes previously planned durable state. It does not plan new work on the fly.

## Example workflow

```bash
source .venv/bin/activate
cp .env.sample .env
# Edit .env with PostgreSQL connection details first.
# IMPORTANT: Create the PostgreSQL database before running migrations.
# For example, if using the default media_manager_db:
#   createdb media_manager_db
# Ensure the database and connection details in .env match before proceeding.

alembic upgrade head
media-manager-api &
# Review the API response and note data.result.run_id from the plan request.

curl -X POST http://127.0.0.1:8000/api/plan \
  -H 'Content-Type: application/json' \
  -d '{"folder_path":"/data/inbox","strict_metadata":false}'

curl -X POST http://127.0.0.1:8000/api/apply \
  -H 'Content-Type: application/json' \
  -d '{"run_id":"11111111-1111-1111-1111-111111111111","collision_mode":"rename"}'
```

Success on a first run means:

- `plan` completes with a `Run ID`.
- `apply` completes without unexpected filesystem mutation outside planned targets.
- rerunning from a durable state boundary remains safe if a run is interrupted.

For more guided walkthroughs, start with [Quickstart](documentation/getting-started/quickstart.md) and [First Run](documentation/getting-started/first-run.md).

## Operator console and API

The operator console and API are for monitoring, policy control, run triggering, diagnostics, and administrative workflows. The console, admin scripts, and automation act as HTTP clients of the same `/api/*` service surface. They are not a shortcut around the runtime invariants; they sit on top of the same safety model.

Operator-facing entry points:

- `/admin/diagnostics`
- `/api/status`
- `/api/runs`
- `/api/policy`
- `/api/run`
- `/api/admin/observability/summary`
- `/api/admin/benchmarks/runs`
- `/metrics`

Use these docs for operational details instead of relying on the README for endpoint-by-endpoint behavior:

- [Operator Guide](documentation/operator-guide/index.md)
- [Operator Console API](documentation/api/api-operator-console.md)
- [Observability guide](documentation/operator-guide/observability.md)

Internal note:

- The supported benchmark interface is the admin API plus `media-manager-benchmark-worker`. The old `tools/perf/*` scripts have been removed.

## Project structure

```text
media-manager/
├── media_manager/        # Core application, persistence, planner, apply, tests
├── operator_console/     # FastAPI app and React operator console integration
├── documentation/        # User, operator, API, architecture, and reference docs
├── migrations/           # Alembic migrations
├── tools/                # Local tooling and support scripts
├── artifacts/            # Generated artifacts and run outputs
├── README.md             # Project entrypoint
├── AGENTS.md             # Runtime invariants and agent safety rules
└── CONTRIBUTING.md       # Contribution workflow
```

## Documentation map

- [Getting Started](documentation/getting-started/index.md)
- [Guides](documentation/guides/index.md)
- [Operator Guide](documentation/operator-guide/index.md)
- [API Documentation](documentation/api/index.md)
- [Architecture](documentation/architecture/index.md)
- [Reference](documentation/reference/index.md)
- [Examples](documentation/examples/index.md)
- [Contributing](documentation/contributing/index.md)

The docs site home is [documentation/home.md](documentation/home.md).

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
./.venv/bin/python -m pytest
```

Tests expect `TEST_DATABASE_URL` to point at a PostgreSQL database prepared for local test runs.

Build the docs:

```bash
./.venv/bin/python -m mkdocs build --strict
```

Contribution workflow, branch conventions, review expectations, and merge policy are documented in [CONTRIBUTING.md](CONTRIBUTING.md). The public contribution process is still settling; use the existing docs as the current baseline rather than a final external contributor guide.

## Safety model and invariants

Before changing code or runtime behavior, read [AGENTS.md](AGENTS.md). It is the repository’s single source of truth for invariants such as:

- no filesystem mutation without durable DB gating
- explicit state transitions
- restart-safe apply behavior
- idempotent operations
- durable failure facts

This matters for code changes, operational tooling, and documentation that describes system behavior.

## License

This repository is licensed under the [MIT License](LICENSE).

In practical terms, that means:

- you may use, copy, modify, merge, publish, distribute, sublicense, and sell the software
- you must keep the copyright and license notice with substantial portions of the software
- the software is provided "as is", without warranty

Review the full license text in [LICENSE](LICENSE) for the exact terms.

## Status and roadmap

The project already has a substantial persistence, operator-console, and documentation surface area, and the current work is focused on hardening API-first workflows, operator playbooks, and documentation quality rather than introducing a brand-new skeleton.

For current documentation priorities, see the [Documentation Roadmap](documentation/roadmap/index.md).

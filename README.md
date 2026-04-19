# refinery-pipeline

Autonomous precious metal swing trading bot

## Setup

```bash
uv sync
```

## Usage

```bash
# Trade pipeline
just run                              # run with defaults
just run --input data/in.json         # specify input
just run --output data/out.json       # specify output
just run --dry-run                    # preview without side effects

# Shortlist pipeline
just shortlist                        # run shortlist pipeline
just shortlist --dry-run              # preview shortlist without side effects
```

## Scheduling (macOS)

The pipeline can be scheduled as a local launchd job using the cron expression configured at project generation time.

```bash
just schedule         # install and activate the launchd job
just schedule-status  # check if the job is loaded
just logs             # tail the stdout log
just unschedule       # remove the job
```

Logs are written to `~/Library/Logs/refinery-pipeline/`.

## Development

```bash
just install    # install all dependencies
just lint       # run pre-commit hooks
just test       # run tests with coverage
just coverage   # generate HTML coverage report
```

## Adding a Component

See `CLAUDE.md` for the three-file component pattern (`protocol.py` → `basic.py` → `__init__.py`).

## License

MIT — see `LICENSE.md`.

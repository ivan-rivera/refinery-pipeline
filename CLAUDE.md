# Project Rules

## Context Documents

Read these before making architectural decisions or starting non-trivial work:

- `docs/ARCHITECTURE.md` — system design, data flow, agent pipeline, tech stack decisions
- `docs/WORK.md` — current task backlog, in-progress work, and what's done
- `docs/DECISIONS.md` — architectural decision log (ADRs)

## Project Summary

Autonomous swing trading bot for precious metals (NYSE, NYSE Arca, NASDAQ). Runs as a scheduled Python job. Uses PydanticAI agents over OpenRouter LLMs. Trades via Alpaca. Data from Finnhub, TwelveData, Reddit. Stores state in SQLite, ChromaDB and Google Sheets.

## General
- Do not modify unrelated files
- Respect existing project structure and patterns
- Avoid overengineering MVP features
- Before any architectural decision, check `docs/DECISIONS.md` to avoid re-litigating settled questions
- Record new architectural decisions as ADRs in `docs/DECISIONS.md`


## Python Style (applies to *.py files)
- Follow the Google Python Style Guide
- Use "double quotes" for strings
- Prefer explicit imports
- Keep functions short and composable
- Avoid magic numbers — put constants in `src/constants.py`
- Prefer small, surgical changes over large rewrites

## Testing (applies to tests/*.py)
- Use pytest for testing, NEVER use unittest or import from it
- Write tests for new functionality
- Write the shortest, most minimalist tests possible that cover core functionality
- Use coverage.py to track test coverage
- Use pytest-cov to report test coverage
- Use pytest-mock to mock dependencies

## PydanticAI Agent Conventions (applies to src/components/agents/**/*.py)

Each agent module must define, in order: a typed `Deps` dataclass, a `Result(BaseModel)`, the `Agent` instance, tool functions, and an async `run_<name>` entrypoint.

- `Deps` must be a typed dataclass — never `dict` or `Any`
- All result models must include `confidence: float` (0.0–1.0)
- Use `@agent.tool` when the tool needs `RunContext`; use `@agent.tool_plain` when it does not
- Every tool must have a docstring — it becomes the tool description sent to the LLM
- Dynamic system prompts that depend on runtime state use `@agent.system_prompt(dynamic=True)`
- Raise `ModelRetry` inside a tool to signal the LLM should retry with corrected input
- Multi-agent: subagents are called via tools on the supervisor agent; each subagent result is serialised to JSON before being passed up
- The supervisor is the only agent that may call the trader agent

## CLI (applies to src/pipeline.py)
- This project uses `click` for CLI argument and option parsing
- The `cli` group is the entrypoint; subcommands are decorated with `@cli.command()`
- Pass click context or options explicitly into components — do not read from env inside components

## Components (applies to src/components/**)
Each component lives in its own directory under `src/components/` and follows this structure:

- `protocol.py` — defines a `Protocol` class (e.g. `FilterFn`) that specifies the callable signature all implementations must match
- `basic.py` — one or more concrete implementations that satisfy the protocol
- `__init__.py` — exports a single orchestrator function (same name as the component, e.g. `filter`, `transform`) that accepts `data` and an optional `fns` sequence defaulting to `_DEFAULT`; applies each fn sequentially so the output of one becomes the input of the next

To add a new implementation: create a new `.py` file in the component directory, implement a function matching the protocol, and add it to `_DEFAULT` in `__init__.py` (or pass it explicitly at the call site).

To add a new component: create a new directory under `src/components/` following the same three-file structure.

# Project Rules

## General
- Do not modify unrelated files
- Respect existing project structure and patterns
- Avoid overengineering MVP features

## Python Style (applies to *.py files)
- Follow the Google Python Style Guide
- Use "double quotes" for strings
- Prefer explicit imports
- Keep functions short and composable
- Avoid magic numbers — put constants in `src/config.py`
- Prefer small, surgical changes over large rewrites

## Testing (applies to tests/*.py)
- Use pytest for testing, NEVER use unittest or import from it
- Write tests for new functionality
- Write the shortest, most minimalist tests possible that cover core functionality
- Use coverage.py to track test coverage
- Use pytest-cov to report test coverage
- Use pytest-mock to mock dependencies

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

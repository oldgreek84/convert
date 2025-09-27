# Agent Guide

## Commands
- **Tests**: `uv run pytest` (run all tests) or `uv run pytest tests/test_converter.py::ConverterTestCase::test_main_convert` (single test)
- **Type checking**: `uv run mypy .` (uses tool.mypy config from pyproject.toml)
- **Linting**: `uv run ruff check .` and `uv run ruff format .` (uses double quotes)
- **Run**: `uv run main.py`
- **Fix lint**: `/fix-lint` (OpenCode agent to automatically fix linting issues)

## Code Style
- **Imports**: Use `from __future__ import annotations` at top, group stdlib/3rd-party/local imports
- **Types**: Use type hints, Protocol for interfaces, dataclasses for config objects
- **Naming**: snake_case for variables/functions/modules, PascalCase for classes
- **Strings**: Double quotes (ruff enforced)
- **Interfaces**: Use ABC with Protocol suffix (e.g., SaverProtocol, UIProtocol)
- **Error handling**: Custom exception classes inherit from Exception, specific error messages

## Architecture
- Interface-based design with protocols in `interfaces/` directory
- Dependency injection via constructor (Converter takes interface, processor, saver, worker)
- Config objects use dataclasses (JobConfig, Target) 
- Use **kwargs in setup methods for extensibility (open-closed principle)

## Key Patterns
- Protocol interfaces for pluggable components (UI, Processor, Saver, Worker)
- Factory pattern for different processor/saver implementations
- Observer pattern in workers/ for async processing
- Configuration objects with validation methods

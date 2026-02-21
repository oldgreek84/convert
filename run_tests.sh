#!/bin/bash
uv run pytest tests/ -v --cov=src --cov=uis --cov=processors --cov-report=term-missing "$@"

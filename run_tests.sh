#!/bin/bash
# Quick test runner script for slackker package

echo "==================================="
echo "Slackker Test Suite Runner"
echo "==================================="
echo ""

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "❌ uv is not installed. Install it from https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

# Run tests with verbose output and coverage
uv run pytest tests/ -v --tb=short --cov=slackker --cov-report=term-missing

echo ""
echo "✅ Test suite completed!"
echo ""
echo "For coverage report in HTML format, run:"
echo "  uv run pytest tests/ --cov=slackker --cov-report=html"
echo ""
echo "For specific test file:"
echo "  uv run pytest tests/test_basic.py -v"

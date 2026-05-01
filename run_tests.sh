#!/bin/bash
# Quick test runner script for slackker package

echo "==================================="
echo "Slackker Test Suite Runner"
echo "==================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest is not installed. Installing now..."
    pip install pytest pytest-cov
fi

echo "📋 Running test suite..."
echo ""

# Run tests with verbose output and coverage
pytest tests/ -v --tb=short --cov=slackker --cov-report=term-missing

echo ""
echo "✅ Test suite completed!"
echo ""
echo "For coverage report in HTML format, run:"
echo "  pytest tests/ --cov=slackker --cov-report=html"
echo ""
echo "For specific test file:"
echo "  pytest tests/test_basic.py -v"

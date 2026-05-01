# Slackker Tests

This directory contains comprehensive unit and integration tests for the slackker package.

## Test Structure

- `test_basic.py` - Tests for the basic callback functions (`SlackUpdate` and `TelegramUpdate`)

## Test Classes

### SlackUpdate Tests
- `TestSlackUpdateInitialization` - Tests for SlackUpdate class initialization
- `TestSlackUpdateNotifierDecorator` - Tests for the notifier decorator
- `TestSlackUpdateNotifyMethod` - Tests for the notify method

### TelegramUpdate Tests
- `TestTelegramUpdateInitialization` - Tests for TelegramUpdate class initialization
- `TestTelegramUpdateNotifierDecorator` - Tests for the notifier decorator
- `TestTelegramUpdateNotifyMethod` - Tests for the notify method

### Integration Tests
- `TestIntegrationScenarios` - End-to-end workflow tests
- `TestEdgeCases` - Edge case and error handling tests
- `TestVerboseLevels` - Tests for different verbose levels

## Running Tests

### Install Test Dependencies
```bash
pip install pytest pytest-cov
```

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test File
```bash
pytest tests/test_basic.py -v
```

### Run Specific Test Class
```bash
pytest tests/test_basic.py::TestSlackUpdateInitialization -v
```

### Run Specific Test Function
```bash
pytest tests/test_basic.py::TestSlackUpdateInitialization::test_slack_update_init_success -v
```

### Run with Coverage Report
```bash
pytest --cov=slackker --cov-report=html
```

### Run Tests Matching a Pattern
```bash
pytest -k "telegram" -v
```

## Test Coverage

The test suite provides comprehensive coverage including:

- ✅ Initialization with valid/invalid tokens
- ✅ Internet connectivity checks
- ✅ API connection validation
- ✅ Notifier decorator with various return types (tuple, single, None)
- ✅ Function argument passing and execution time tracking
- ✅ Notify method with args and kwargs
- ✅ Timestamp generation
- ✅ Verbose logging at different levels
- ✅ Error handling and exceptions
- ✅ Integration workflows
- ✅ Edge cases (empty tuples, dicts, lists)

## Mocking Strategy

All external API calls are mocked using `unittest.mock`:
- Slack API calls via `WebClient`
- Telegram API calls via HTTP requests
- Internet connectivity checks
- Chat ID retrieval

This allows tests to run without requiring actual API tokens or internet connectivity.

## Example Test Usage

```python
from slackker.callbacks.basic import TelegramUpdate

# Example from the test suite
@pytest.mark.parametrize("token,expected", [
    ("1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG", True),
    (None, False),
])
def test_telegram_token_validation(token, expected):
    # Test implementation
    pass
```

## Contributing

When adding new tests:
1. Follow the existing test class organization
2. Use descriptive test names with `test_` prefix
3. Mock external dependencies to avoid side effects
4. Include docstrings explaining what is being tested
5. Test both success and failure scenarios

# Slackker Tests

This folder contains the complete test suite for `slackker`. All test documentation is consolidated in this single file.

## Test Files

- `test_basic.py`: Basic callback tests (`SlackUpdate`, `TelegramUpdate`) for decorators and script notifications.
- `test_keras.py`: Keras callback tests (`SlackUpdate`, `TelegramUpdate`) for train lifecycle reporting.
- `test_lightning.py`: Lightning callback tests (`SlackUpdate`, `TelegramUpdate`) for fit lifecycle reporting.
- `conftest.py`: Shared pytest setup.

## Coverage Summary

### Basic Callback Coverage

- Initialization checks (token, connectivity, API validation)
- `notifier` decorator behavior (tuple/single/None returns)
- Execution time and message generation
- `notify(*args, **kwargs)` formatting and timestamp behavior
- Error and edge scenarios

### Keras Callback Coverage

- Callback initialization and argument handling
- `on_train_begin`, `on_epoch_end`, `on_train_end`
- Training history tracking and best-epoch reporting
- Plot-history dispatch calls
- Verbose mode and edge cases

### Lightning Callback Coverage

- Callback initialization and validation for `TrackLogs` and `monitor`
- `on_fit_start`, `on_train_epoch_end`, `on_fit_end`
- Per-epoch metric extraction from `trainer.callback_metrics`
- Best epoch selection for loss and accuracy monitors
- Reference workflow simulation from a `Trainer(max_epochs=...)` style run

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-cov
# or
pip install -e ".[test]"
```

### Run All Tests

```bash
pytest
pytest -v
pytest --cov=slackker --cov-report=term-missing
```

### Run By Module

```bash
pytest tests/test_basic.py -v
pytest tests/test_keras.py -v
pytest tests/test_lightning.py -v
```

### Run By Pattern

```bash
pytest -k "telegram" -v
pytest -k "keras" -v
pytest -k "lightning" -v
pytest -k "integration" -v
```

### Coverage HTML Report

```bash
pytest --cov=slackker --cov-report=html
```

## Mocking Strategy

Tests use `unittest.mock` to isolate external dependencies:

- Slack client calls (`WebClient`, Slack reporting helpers)
- Telegram API helpers
- Connectivity checks
- Plot upload/report helpers

This keeps tests deterministic and runnable without real tokens or network access.

## Adding New Tests

1. Follow existing naming: `test_<behavior>`.
2. Keep tests focused on one behavior.
3. Mock external I/O and network calls.
4. Assert both side effects and message content when relevant.
5. Add edge-case coverage for new callback paths.

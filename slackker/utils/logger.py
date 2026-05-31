import sys

from loguru import logger

# Remove default handler
logger.remove()


def _is_slackker_record(record) -> bool:
    return record["extra"].get("name") == "slackker"


def _is_always_record(record) -> bool:
    return _is_slackker_record(record) and bool(record["extra"].get("always", False))


def _is_regular_record(record) -> bool:
    return _is_slackker_record(record) and not bool(
        record["extra"].get("always", False)
    )


def set_verbosity(verbose: int):
    """
    Sets the logging verbosity level for the slackker package.

    - 0: WARNING and ERROR
    - 1: INFO, WARNING, and ERROR
    - 2: DEBUG, INFO, WARNING, and ERROR

    Records logged with ``extra={"always": True}`` are always emitted at INFO+
    regardless of verbosity.
    """
    levels = {
        0: "WARNING",
        1: "INFO",
        2: "DEBUG",
    }
    level = levels.get(verbose, "WARNING")

    # Remove all handlers to update the level
    logger.remove()

    # Always-visible slackker logs (e.g., critical lifecycle messages)
    logger.add(
        sys.stderr,
        format="<level>[slackker] {level}: {message}</level>",
        level="INFO",
        filter=_is_always_record,
    )

    # Regular verbosity-controlled slackker logs
    logger.add(
        sys.stderr,
        format="<level>[slackker] {level}: {message}</level>",
        level=level,
        filter=_is_regular_record,
    )


# Initialize with default verbosity (0)
set_verbosity(0)

# Expose a module-level logger bound to slackker namespace
log = logger.bind(name="slackker")

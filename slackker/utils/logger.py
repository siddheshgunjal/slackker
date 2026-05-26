import sys

from loguru import logger

# Remove default handler
logger.remove()


def set_verbosity(verbose: int):
    """
    Sets the logging verbosity level for the slackker package.

    - 0: WARNING and ERROR
    - 1: INFO, WARNING, and ERROR
    - 2: DEBUG, INFO, WARNING, and ERROR
    """
    levels = {
        0: "WARNING",
        1: "INFO",
        2: "DEBUG",
    }
    level = levels.get(verbose, "WARNING")

    # Remove all handlers to update the level
    logger.remove()

    # Add slackker-prefixed handler
    logger.add(
        sys.stderr,
        format="<level>[slackker] {level}: {message}</level>",
        level=level,
        filter=lambda record: record["extra"].get("name") == "slackker",
    )


# Initialize with default verbosity (0)
set_verbosity(0)

# Expose a module-level logger bound to slackker namespace
log = logger.bind(name="slackker")

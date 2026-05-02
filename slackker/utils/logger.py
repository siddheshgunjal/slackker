import sys
from loguru import logger

# Remove default handler
logger.remove()

# Add slackker-prefixed handler
logger.add(
    sys.stderr,
    format="<level>[slackker] {level}: {message}</level>",
    level="DEBUG",
    filter="slackker",
)

# Expose a module-level logger bound to slackker namespace
log = logger.bind(name="slackker")

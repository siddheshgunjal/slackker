import asyncio
import httpx
from slack_sdk.web.async_client import AsyncWebClient
from slackker.utils.logger import log


def _run_sync(coro):
    """Run an async coroutine synchronously, handling already-running event loops (e.g. Jupyter)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        import nest_asyncio
        nest_asyncio.apply()
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)


async def check_connection(url: str, retries: int = 0, delay: float = 60, verbose: int = 2) -> bool:
    """Check if a server is reachable. Retries indefinitely if retries=0, else up to `retries` times."""
    attempt = 0
    async with httpx.AsyncClient() as client:
        while True:
            attempt += 1
            try:
                resp = await client.head(f"https://{url}", timeout=5)
                if verbose >= 2:
                    log.debug(f"Connection to '{url}' server successful!")
                return True
            except (httpx.RequestError, httpx.HTTPStatusError):
                if retries > 0 and attempt >= retries:
                    if verbose >= 1:
                        log.warning(
                            f"Connection to '{url}' server failed after {attempt} attempts."
                        )
                    return False
                if verbose >= 1:
                    log.warning(
                        f"Connection to '{url}' server failed. "
                        f"Trying again in {delay}s.. [attempt {attempt}]"
                    )
                await asyncio.sleep(delay)


async def check_connection_quick(url: str, max_retries: int = 3, delay: float = 10, verbose: int = 1) -> bool:
    """Quick connectivity check with limited retries (for use during training epochs)."""
    return await check_connection(url=url, retries=max_retries, delay=delay, verbose=verbose)


async def verify_slack_token(token: str, verbose: int = 2) -> bool:
    """Verify a Slack API token by calling api.test."""
    try:
        client = AsyncWebClient(token=token)
        response = await client.api_test()
        await client.close()
        if verbose >= 2:
            log.debug(f"Connection to Slack API successful! {response}")
        return True
    except Exception as e:
        log.error(f"Invalid Slack API token: {e}")
        return False


async def get_telegram_chat_id(token: str, verbose: int = 2) -> str | None:
    """Retrieve the chat_id from the first message sent to the Telegram bot."""
    url = f"https://api.telegram.org/bot{token}/getUpdates"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            data = resp.json()
            chat_id = str(data["result"][0]["message"]["chat"]["id"])
            if verbose >= 2:
                log.debug("Connection to Telegram API successful!")
                log.debug(f"Found chat with 'chat_id'={chat_id}")
            return chat_id
    except Exception as e:
        log.error(f"Could not connect to Telegram API: {e}")
        log.warning("Please send 'Hello' once to your bot to make it discoverable to slackker")
        return None


# --- Sync wrappers ---

def check_connection_sync(url: str, retries: int = 0, delay: float = 60, verbose: int = 2) -> bool:
    return _run_sync(check_connection(url, retries, delay, verbose))


def check_connection_quick_sync(url: str, max_retries: int = 3, delay: float = 10, verbose: int = 1) -> bool:
    return _run_sync(check_connection_quick(url, max_retries, delay, verbose))


def verify_slack_token_sync(token: str, verbose: int = 2) -> bool:
    return _run_sync(verify_slack_token(token, verbose))


def get_telegram_chat_id_sync(token: str, verbose: int = 2) -> str | None:
    return _run_sync(get_telegram_chat_id(token, verbose))

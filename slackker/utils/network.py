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


async def get_teams_device_code(
    app_id: str,
    tenant_id: str,
    scopes: list[str],
    verbose: int = 2,
) -> dict | None:
    """Request a device code for interactive Microsoft Graph authentication.

    Returns the device code response dict (contains ``user_code``,
    ``device_code``, ``verification_uri``, ``message``, ``interval``,
    ``expires_in``) on success, or ``None`` on failure.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/devicecode"
    payload = {
        "client_id": app_id,
        "scope": " ".join(scopes),
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            if verbose >= 2:
                log.debug("Teams: Device code obtained successfully.")
            return resp.json()
    except httpx.HTTPStatusError as e:
        log.error(f"Teams: Failed to get device code ({e.response.status_code}): {e.response.text}")
        return None
    except Exception as e:
        log.error(f"Teams: Failed to get device code: {e}")
        return None


async def poll_teams_device_code_token(
    app_id: str,
    tenant_id: str,
    device_code: str,
    interval: int = 5,
    verbose: int = 2,
) -> dict | None:
    """Poll for a token after the user completes device code authorisation.

    Blocks (with async sleep) until the user authenticates, the code
    expires, or authorisation is declined. Returns the token response dict
    (contains ``access_token``, ``refresh_token``, ``expires_in``) on
    success, or ``None`` on failure.
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "client_id": app_id,
        "device_code": device_code,
    }
    poll_interval = max(interval, 5)
    async with httpx.AsyncClient() as client:
        while True:
            await asyncio.sleep(poll_interval)
            try:
                resp = await client.post(url, data=payload, timeout=10)
                data = resp.json()
            except Exception as e:
                log.error(f"Teams: Poll request failed: {e}")
                return None

            if "access_token" in data:
                if verbose >= 2:
                    log.debug("Teams: Device code authentication successful.")
                return data

            error = data.get("error", "")
            if error == "authorization_pending":
                continue
            elif error == "slow_down":
                poll_interval += 5
                continue
            else:
                # authorization_declined, expired_token, bad_verification_code
                log.error(f"Teams: Authentication failed: {data.get('error_description', error)}")
                return None


async def refresh_teams_access_token(
    app_id: str,
    tenant_id: str,
    refresh_token: str,
    scopes: list[str],
    verbose: int = 2,
) -> dict | None:
    """Silently refresh a Microsoft Graph access token using a cached refresh token.

    Returns the new token response dict on success, or ``None`` if the
    refresh token is expired or invalid (caller should trigger a new device
    code flow).
    """
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    payload = {
        "grant_type": "refresh_token",
        "client_id": app_id,
        "refresh_token": refresh_token,
        "scope": " ".join(scopes),
    }
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            if "access_token" in data:
                if verbose >= 2:
                    log.debug("Teams: Access token refreshed silently.")
                return data
            log.error(f"Teams: Token refresh returned no access_token: {data}")
            return None
    except httpx.HTTPStatusError as e:
        if verbose >= 1:
            log.warning(f"Teams: Token refresh failed ({e.response.status_code}), re-authentication required.")
        return None
    except Exception as e:
        log.error(f"Teams: Token refresh error: {e}")
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


def get_teams_device_code_sync(
    app_id: str, tenant_id: str, scopes: list[str], verbose: int = 2
) -> dict | None:
    return _run_sync(get_teams_device_code(app_id, tenant_id, scopes, verbose))


def poll_teams_device_code_token_sync(
    app_id: str, tenant_id: str, device_code: str, interval: int = 5, verbose: int = 2
) -> dict | None:
    return _run_sync(poll_teams_device_code_token(app_id, tenant_id, device_code, interval, verbose))


def refresh_teams_access_token_sync(
    app_id: str, tenant_id: str, refresh_token: str, scopes: list[str], verbose: int = 2
) -> dict | None:
    return _run_sync(refresh_teams_access_token(app_id, tenant_id, refresh_token, scopes, verbose))

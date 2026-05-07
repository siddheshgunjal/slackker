import json
import os
import time
import httpx
from pathlib import Path
from slackker.core.client import BaseClient
from slackker.utils.logger import log
from slackker.utils import network

_GRAPH_BASE = "https://graph.microsoft.com/v1.0"


class TeamsClient(BaseClient):
    """Microsoft Teams client backend using the Microsoft Graph API.

    Uses OAuth 2.0 **device code flow** — no app secret or admin consent
    required. On the first call to ``connect()``, a one-time interactive
    login is triggered: a URL and short code are printed to stdout, the user
    visits the URL, enters the code, and signs in with a **work or school
    Microsoft 365 account**. The resulting token is cached on disk and
    silently refreshed on subsequent runs — no login prompt after the first
    time.

    .. note::
        Personal Microsoft accounts (Outlook.com, Hotmail, Live.com) are
        **not supported**. The Microsoft Graph Chat API
        (``/chats/{id}/messages``) requires a work or school account backed
        by an Entra ID (Azure AD) tenant. Attempting to authenticate with a
        personal account will succeed at the OAuth step but fail with a 403
        or 404 when posting to Teams chat.

    File uploads are stored in the authenticated user's OneDrive via
    Microsoft Graph and referenced as a link in the chat message.

    Parameters
    ----------
    app_id : str
        Azure AD application (client) ID from your app registration.
        The app must have ``Chat.ReadWrite``, ``Files.ReadWrite``,
        ``offline_access``, and ``User.Read`` **delegated** permissions
        (no admin consent required for these).
    tenant_id : str
        Azure AD tenant ID, or ``"common"`` *(default)* to accept both
        work/school and personal account sign-in flows at the OAuth level.
        Note that even with ``"common"``, the Graph Chat API only works for
        work or school accounts. If all your users are on a single tenant,
        pass the tenant's ID or domain (e.g. ``"contoso.onmicrosoft.com"``)
        to restrict sign-in to that organisation.
    chat_id : str
        The Teams personal chat ID (e.g. ``'19:..._...@thread.v2'``).
        In Microsoft Teams, right-click a message in the target chat and
        choose "Copy link to message". The chat ID is embedded in the URL
        and typically starts with ``19:`` and ends with ``@thread.v2``.
    token_cache_path : str, optional
        Path to a JSON file for caching the access/refresh token.
        Defaults to ``~/.slackker/teams_<first-8-chars-of-app_id>.json``.
    verbose : int
        Logging verbosity (0 = silent, 1 = info, 2 = debug).
    """

    _SCOPES = ["Chat.ReadWrite", "Files.ReadWrite", "offline_access", "User.Read"]

    def __init__(
        self,
        app_id: str,
        tenant_id: str = "common",
        chat_id: str = "",
        token_cache_path: str | None = None,
        verbose: int = 0,
    ):
        super().__init__(verbose=verbose)
        if not app_id:
            raise ValueError("Microsoft Teams app_id (Azure AD client ID) is required.")
        if not chat_id:
            raise ValueError(
                "Microsoft Teams chat_id is required. "
                "In Teams, right-click a message in the target chat and use "
                "'Copy link to message'; extract the chat ID from the URL "
                "(usually starts with '19:' and ends with '@thread.v2')."
            )

        self._app_id = app_id
        self._tenant_id = tenant_id
        self._chat_id = chat_id
        self._cache_path = (
            Path(token_cache_path)
            if token_cache_path
            else Path.home() / ".slackker" / f"teams_{app_id[:8]}.json"
        )

        self._access_token: str | None = None
        self._token_expiry: float = 0.0

    # ── Abstract property implementations ──────────────────────────────────

    @property
    def platform(self) -> str:
        return "teams"

    @property
    def is_connected(self) -> bool:
        return self._access_token is not None and time.time() < self._token_expiry

    @property
    def connectivity_url(self) -> str:
        return "graph.microsoft.com"

    # ── Public read-only properties ─────────────────────────────────────────

    @property
    def chat_id(self) -> str:
        return self._chat_id

    # ── Token cache helpers ─────────────────────────────────────────────────

    def _load_token_cache(self) -> dict | None:
        """Load cached token data from disk. Returns None if missing or unreadable."""
        try:
            if self._cache_path.is_file():
                with open(self._cache_path) as f:
                    return json.load(f)
        except Exception:
            pass
        return None

    def _save_token_cache(self, data: dict) -> None:
        """Persist token data to disk, creating parent directories as needed."""
        try:
            self._cache_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._cache_path, "w") as f:
                json.dump(data, f)
        except Exception as e:
            log.warning(f"Teams: Could not save token cache to {self._cache_path}: {e}")

    def _apply_token(self, token_data: dict) -> None:
        """Store token in memory and persist refresh token to disk cache."""
        self._access_token = token_data["access_token"]
        expires_in = int(token_data.get("expires_in", 3600))
        self._token_expiry = time.time() + expires_in - 300  # 5-min safety buffer
        self._save_token_cache({
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "expires_at": self._token_expiry,
        })

    # ── Connection ──────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """Authenticate with Microsoft Graph and verify connectivity.

        Flow:
        1. Check reachability of ``graph.microsoft.com``.
        2. Attempt a silent token refresh using any cached refresh token.
        3. If no cache or refresh fails, start the device code flow:
           a. Print a short URL + code for the user to visit once.
           b. Poll until the user authenticates or the code expires.
        4. Cache the resulting token for future silent refreshes.
        """
        server = await network.check_connection(url="graph.microsoft.com", verbose=self._verbose)
        if not server:
            return False

        # Try silent refresh first
        cached = self._load_token_cache()
        if cached and cached.get("refresh_token"):
            refreshed = await network.refresh_teams_access_token(
                app_id=self._app_id,
                tenant_id=self._tenant_id,
                refresh_token=cached["refresh_token"],
                scopes=self._SCOPES,
                verbose=self._verbose,
            )
            if refreshed:
                self._apply_token(refreshed)
                if self._verbose >= 1:
                    log.info("Teams: Authenticated via cached token.")
                return True

        # Interactive device code flow
        code_data = await network.get_teams_device_code(
            app_id=self._app_id,
            tenant_id=self._tenant_id,
            scopes=self._SCOPES,
            verbose=self._verbose,
        )
        if not code_data:
            return False

        # Always print — user must see this to complete auth
        print(f"\n{code_data['message']}\n")

        token_data = await network.poll_teams_device_code_token(
            app_id=self._app_id,
            tenant_id=self._tenant_id,
            device_code=code_data["device_code"],
            interval=int(code_data.get("interval", 5)),
            verbose=self._verbose,
        )
        if not token_data:
            return False

        self._apply_token(token_data)
        if self._verbose >= 1:
            log.info("Teams: Authenticated successfully via device code flow.")
        return True

    # ── Token management ────────────────────────────────────────────────────

    async def _ensure_token(self) -> bool:
        """Re-acquire token if expired or missing."""
        if self.is_connected:
            return True
        return await self.connect()

    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    # ── Messaging ───────────────────────────────────────────────────────────

    async def send_message(self, text: str) -> None:
        """Send a plain-text message to the configured personal chat."""
        if not await self._ensure_token():
            log.error("Teams: Cannot send message — not connected.")
            return

        url = f"{_GRAPH_BASE}/chats/{self._chat_id}/messages"
        payload = {"body": {"contentType": "text", "content": text}}
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=self._auth_headers(), timeout=10)
                resp.raise_for_status()
            if self._verbose >= 1:
                log.info("Teams: Message posted to personal chat.")
        except httpx.HTTPStatusError as e:
            log.error(f"Teams: Error posting message ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            log.error(f"Teams: Error posting message: {e}")

    # ── File / image upload ─────────────────────────────────────────────────

    async def upload_file(self, filepath: str, comment: str | None = None) -> None:
        """Upload a file to the authenticated user's OneDrive and post a link in the chat.

        The file is stored under the root of the user's OneDrive using the
        delegated Graph endpoint ``/me/drive/root:/{filename}:/content``.
        """
        if not os.path.isfile(filepath):
            log.error(f"Teams: Invalid file path: {filepath}")
            return

        if not await self._ensure_token():
            log.error("Teams: Cannot upload file — not connected.")
            return

        filename = os.path.basename(filepath)
        upload_url = f"{_GRAPH_BASE}/me/drive/root:/{filename}:/content"

        try:
            with open(filepath, "rb") as f:
                file_bytes = f.read()

            async with httpx.AsyncClient() as client:
                resp = await client.put(
                    upload_url,
                    content=file_bytes,
                    headers={
                        "Authorization": f"Bearer {self._access_token}",
                        "Content-Type": "application/octet-stream",
                    },
                    timeout=60,
                )
                resp.raise_for_status()
                web_url = resp.json().get("webUrl", "")

            if self._verbose >= 1:
                log.debug(f"Teams: Uploaded '{filename}' to OneDrive.")

            caption = comment or f"Attachment: {filename}"
            message_text = f"{caption}\n{web_url}" if web_url else caption
            await self.send_message(message_text)

        except httpx.HTTPStatusError as e:
            log.error(f"Teams: Error uploading file ({e.response.status_code}): {e.response.text}")
        except Exception as e:
            log.error(f"Teams: Error uploading file: {e}")

    async def upload_image(self, filepath: str, comment: str | None = None) -> None:
        """Upload an image — treated identically to upload_file for Teams."""
        await self.upload_file(filepath, comment)
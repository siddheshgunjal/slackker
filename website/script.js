const menuButton = document.getElementById("menuButton");
const navLinks = document.getElementById("navLinks");
const year = document.getElementById("year");

function closeNav() {
  menuButton.setAttribute("aria-expanded", "false");
  navLinks.classList.remove("open");
}

if (menuButton && navLinks) {
  menuButton.addEventListener("click", () => {
    const expanded = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!expanded));
    navLinks.classList.toggle("open");
  });

  // Close mobile nav when any nav link is clicked
  navLinks.querySelectorAll("a").forEach((link) => {
    link.addEventListener("click", closeNav);
  });
}

if (year) {
  year.textContent = new Date().getFullYear();
}

async function updateVersion() {
  const versionElement = document.getElementById("version");
  const ldJsonElement = document.getElementById("ld-json");

  try {
    const response = await fetch("https://pypi.org/pypi/slackker/json");
    if (!response.ok) throw new Error("Network response was not ok");
    const data = await response.json();
    const version = data.info.version;

    if (versionElement) {
      versionElement.textContent = `slackker v${version}`;
    }

    if (ldJsonElement) {
      try {
        const ldJson = JSON.parse(ldJsonElement.textContent);
        const softwareApp = ldJson["@graph"].find(
          (item) => item["@type"] === "SoftwareApplication",
        );
        if (softwareApp) {
          softwareApp.softwareVersion = version;
          ldJsonElement.textContent = JSON.stringify(ldJson, null, 2);
        }
      } catch (e) {
        console.error("Failed to parse or update JSON-LD:", e);
      }
    }
  } catch (error) {
    console.error("Failed to fetch version from PyPI:", error);
  }
}

updateVersion();

const revealElements = document.querySelectorAll(".reveal");
const revealObserver = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("visible");
        revealObserver.unobserve(entry.target);
      }
    });
  },
  { threshold: 0.15 },
);

revealElements.forEach((element) => revealObserver.observe(element));

const usageSection = document.getElementById("usage");
const tabs = usageSection
  ? usageSection.querySelectorAll(".example-switch .example-tab")
  : [];
const panels = usageSection
  ? usageSection.querySelectorAll(".example-panels .example-panel")
  : [];

function activateTab(targetId) {
  tabs.forEach((tab) => {
    const isActive = tab.dataset.target === targetId;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });

  panels.forEach((panel) => {
    const isActive = panel.id === targetId;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => activateTab(tab.dataset.target));
});

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function highlightPython(codeText) {
  let code = escapeHtml(codeText);
  const placeholders = [];

  const stash = (regex, tokenClass) => {
    code = code.replace(regex, (match) => {
      const idx =
        placeholders.push(`<span class="${tokenClass}">${match}</span>`) - 1;
      return `@@HL${idx}@@`;
    });
  };

  // Protect strings/comments from later substitutions.
  stash(
    /("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g,
    "tok-string",
  );
  stash(/#.*/g, "tok-comment");

  code = code.replace(
    /(^\s*)(@[A-Za-z_][\w.]*)/gm,
    '$1<span class="tok-decorator">$2</span>',
  );
  code = code.replace(
    /\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b/g,
    (m, kw, name) => {
      return `<span class="tok-keyword">${kw}</span> <span class="tok-function">${name}</span>`;
    },
  );
  code = code.replace(
    /\b(from|import|as|if|elif|else|for|while|return|try|except|finally|with|in|pass|raise|break|continue|lambda|and|or|not|is|yield|await|async|global|nonlocal|assert|del)\b/g,
    '<span class="tok-keyword">$1</span>',
  );
  code = code.replace(
    /\b(True|False|None|self)\b/g,
    '<span class="tok-builtin">$1</span>',
  );
  code = code.replace(
    /\b\d+(?:\.\d+)?\b/g,
    '<span class="tok-number">$&</span>',
  );

  code = code.replace(/@@HL(\d+)@@/g, (_, idx) => placeholders[Number(idx)]);
  return code;
}

function applyPythonHighlighting() {
  document.querySelectorAll("code.code-python").forEach((block) => {
    block.innerHTML = highlightPython(block.textContent || "");
  });
}

applyPythonHighlighting();

// ── Platform toggle ───────────────────────────────────────────

const CODE_SNIPPETS = {
  hero: {
    telegram: `from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train_model(epochs=20)`,
    slack: `from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train_model(epochs=20)`,
    teams: `from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    tenant_id="YOUR_TENANT_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train_model(epochs=20)`,
    discord: `from slackker.core import DiscordClient
from slackker.callbacks.simple import SimpleCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train_model(epochs=20)`,
  },
  decorator: {
    telegram: `from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

# Return value is automatically sent as a notification
train_model(epochs=20)`,
    slack: `from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

# Return value is automatically sent as a notification
train_model(epochs=20)`,
    teams: `from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    tenant_id="YOUR_TENANT_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

# Return value is automatically sent as a notification
train_model(epochs=20)`,
    discord: `from slackker.core import DiscordClient
from slackker.callbacks.simple import SimpleCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def train_model(epochs: int):
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

# Return value is automatically sent as a notification
train_model(epochs=20)`,
  },
  notify: {
    telegram: `from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notify = SimpleCallback(client)

def run_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_pipeline("./data/train.csv")
    # Send detailed update with custom fields and file attachment
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
    slack: `from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
notify = SimpleCallback(client)

def run_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_pipeline("./data/train.csv")
    # Send detailed update with custom fields and file attachment
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
    teams: `from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    tenant_id="YOUR_TENANT_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
)
notify = SimpleCallback(client)

def run_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_pipeline("./data/train.csv")
    # Send detailed update with custom fields and file attachment
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
    discord: `from slackker.core import DiscordClient
from slackker.callbacks.simple import SimpleCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
notify = SimpleCallback(client)

def run_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_pipeline("./data/train.csv")
    # Send detailed update with custom fields and file attachment
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
  },
  "pipeline-sync": {
    telegram: `import time
from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notifier = SimpleCallback(client)

def main():
    # Step 1
    notifier.notify("📥 Step 1: Fetching data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 1 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    notifier.notify("⚙️ Step 2: Processing data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 2 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    notifier.stop()

main()`,
    slack: `import time
from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
notifier = SimpleCallback(client)

def main():
    # Step 1
    notifier.notify("📥 Step 1: Fetching data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 1 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    notifier.notify("⚙️ Step 2: Processing data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 2 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    notifier.stop()

main()`,
    teams: `import time
from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    tenant_id="YOUR_TENANT_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
)
notifier = SimpleCallback(client)

def main():
    # Step 1
    notifier.notify("📥 Step 1: Fetching data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 1 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    notifier.notify("⚙️ Step 2: Processing data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 2 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    notifier.stop()

main()`,
    discord: `import time
from slackker.core import DiscordClient
from slackker.callbacks.simple import SimpleCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
notifier = SimpleCallback(client)

def main():
    # Step 1
    notifier.notify("📥 Step 1: Fetching data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 1 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    notifier.notify("⚙️ Step 2: Processing data...", status="started")
    time.sleep(2)
    if not notifier.ask("Step 2 done. Continue?"):
        notifier.stop()
        return
    notifier.notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    notifier.stop()

main()`,
  },
  "pipeline-async": {
    telegram: `import asyncio
from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notifier = SimpleCallback(client)

async def main():
    # Step 1
    await notifier.async_notify("📥 Step 1: Fetching data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 1 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    await notifier.async_notify("⚙️ Step 2: Processing data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 2 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    await notifier.async_stop()

asyncio.run(main())`,
    slack: `import asyncio
from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
notifier = SimpleCallback(client)

async def main():
    # Step 1
    await notifier.async_notify("📥 Step 1: Fetching data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 1 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    await notifier.async_notify("⚙️ Step 2: Processing data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 2 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    await notifier.async_stop()

asyncio.run(main())`,
    teams: `import asyncio
from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    tenant_id="YOUR_TENANT_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
)
notifier = SimpleCallback(client)

async def main():
    # Step 1
    await notifier.async_notify("📥 Step 1: Fetching data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 1 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    await notifier.async_notify("⚙️ Step 2: Processing data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 2 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    await notifier.async_stop()

asyncio.run(main())`,
    discord: `import asyncio
from slackker.core import DiscordClient
from slackker.callbacks.simple import SimpleCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
notifier = SimpleCallback(client)

async def main():
    # Step 1
    await notifier.async_notify("📥 Step 1: Fetching data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 1 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 1: Data fetched", status="completed")

    # Step 2
    await notifier.async_notify("⚙️ Step 2: Processing data...", status="started")
    await asyncio.sleep(2)
    if not await notifier.async_ask("Step 2 done. Continue?"):
        await notifier.async_stop()
        return
    await notifier.async_notify("✅ Step 2: Processing done", status="completed")

    # Done
    notifier.notify(
        "🏁 Pipeline complete",
        message="All steps finished ✅",
        attachment="./report.pdf"
    )
    await notifier.async_stop()

asyncio.run(main())`,
  },
  keras: {
    telegram: `from slackker.core import TelegramClient
from slackker.callbacks.keras import KerasCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
slackker_cb = KerasCallback(
    client=client,
    model_name="ImageClassifierV1",
    export="png",
    send_plot=True,
)

history = model.fit(
    x_train,
    y_train,
    epochs=20,
    batch_size=32,
    validation_data=(x_val, y_val),
    callbacks=[slackker_cb]
)`,
    slack: `from slackker.core import SlackClient
from slackker.callbacks.keras import KerasCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
slackker_cb = KerasCallback(
    client=client,
    model_name="ImageClassifierV1",
    export="png",
    send_plot=True,
)

history = model.fit(
    x_train,
    y_train,
    epochs=20,
    batch_size=32,
    validation_data=(x_val, y_val),
    callbacks=[slackker_cb]
)`,
    teams: `from slackker.core import TeamsClient
from slackker.callbacks.keras import KerasCallback

client = TeamsClient(
  app_id="YOUR_AZURE_APP_ID",
  tenant_id="YOUR_TENANT_ID",
  chat_id="19:abc@thread.v2",
  verbose=1
)
slackker_cb = KerasCallback(
  client=client,
  model_name="ImageClassifierV1",
  export="png",
  send_plot=True,
)

history = model.fit(
  x_train,
  y_train,
  epochs=20,
  batch_size=32,
  validation_data=(x_val, y_val),
  callbacks=[slackker_cb]
)`,
    discord: `from slackker.core import DiscordClient
from slackker.callbacks.keras import KerasCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
slackker_cb = KerasCallback(
    client=client,
    model_name="ImageClassifierV1",
    export="png",
    send_plot=True,
)

history = model.fit(
    x_train,
    y_train,
    epochs=20,
    batch_size=32,
    validation_data=(x_val, y_val),
    callbacks=[slackker_cb]
)`,
  },
  lightning: {
    telegram: `from lightning.pytorch import Trainer
from slackker.core import TelegramClient
from slackker.callbacks.lightning import LightningCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
slackker_cb = LightningCallback(
    client=client,
    model_name="LightningClassifier",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)

trainer = Trainer(max_epochs=12, callbacks=[slackker_cb])
trainer.fit(model, train_loader, val_loader)`,
    slack: `from lightning.pytorch import Trainer
from slackker.core import SlackClient
from slackker.callbacks.lightning import LightningCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel_id="A04AAB77ABC",
    verbose=1
)
slackker_cb = LightningCallback(
    client=client,
    model_name="LightningClassifier",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)

trainer = Trainer(max_epochs=12, callbacks=[slackker_cb])
trainer.fit(model, train_loader, val_loader)`,
    teams: `from lightning.pytorch import Trainer
from slackker.core import TeamsClient
from slackker.callbacks.lightning import LightningCallback

client = TeamsClient(
  app_id="YOUR_AZURE_APP_ID",
  tenant_id="YOUR_TENANT_ID",
  chat_id="19:abc@thread.v2",
  verbose=1
)
slackker_cb = LightningCallback(
  client=client,
  model_name="LightningClassifier",
  track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
  monitor="val_loss",
  export="png",
  send_plot=True,
)

trainer = Trainer(max_epochs=12, callbacks=[slackker_cb])
trainer.fit(model, train_loader, val_loader)`,
    discord: `from lightning.pytorch import Trainer
from slackker.core import DiscordClient
from slackker.callbacks.lightning import LightningCallback

client = DiscordClient(
    token="your_bot_token",
    channel_id="123456789012345678",
    verbose=1
)
slackker_cb = LightningCallback(
    client=client,
    model_name="LightningClassifier",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)

trainer = Trainer(max_epochs=12, callbacks=[slackker_cb])
trainer.fit(model, train_loader, val_loader)`,
  },
  mcp: {
    vscode: `{
  "servers": {
    "slackker": {
      "type": "stdio",
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    zed: `{
  "context_servers": {
    "slackker": {
      "command": {
        "path": "slackker-mcp",
        "env": {
          "SLACKKER_PLATFORM": "slack",
          "SLACKKER_TOKEN": "xoxb-...",
          "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
        }
      }
    }
  }
}`,
    "claude-desktop": `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    "claude-code": `{
  "mcpServers": {
    "slackker": {
      "type": "stdio",
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    opencode: `{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "slackker": {
      "type": "local",
      "command": ["slackker-mcp"],
      "enabled": true,
      "environment": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    roo: `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    cursor: `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    continue: `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    antigravity: `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
    hermes: `{
  "mcpServers": {
    "slackker": {
      "command": "slackker-mcp",
      "env": {
        "SLACKKER_PLATFORM": "slack",
        "SLACKKER_TOKEN": "xoxb-...",
        "SLACKKER_CHANNEL_ID": "C04AAB77ABC"
      }
    }
  }
}`,
  },
};

// ── Setup tab switcher ───────────────────────────────────────
const setupTabs = document.querySelectorAll(".setup-tab");
const setupPanels = document.querySelectorAll(".setup-panel");

function activateSetupTab(targetId) {
  setupTabs.forEach((tab) => {
    const isActive = tab.dataset.target === targetId;
    tab.classList.toggle("active", isActive);
    tab.setAttribute("aria-selected", String(isActive));
  });
  setupPanels.forEach((panel) => {
    const isActive = panel.id === targetId;
    panel.classList.toggle("active", isActive);
    panel.hidden = !isActive;
  });
}

setupTabs.forEach((tab) => {
  tab.addEventListener("click", () => activateSetupTab(tab.dataset.target));
});

// ── Platform toggle ───────────────────────────────────────────
document.querySelectorAll(".platform-toggle").forEach((toggle) => {
  toggle.querySelectorAll(".plt-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const platform = btn.dataset.platform;
      const container = toggle.closest(".hero-code, .example-panel");
      const codeBlock = container.querySelector("code.code-python");
      const snippet = codeBlock.dataset.snippet;

      if (!CODE_SNIPPETS[snippet]?.[platform]) return;

      toggle
        .querySelectorAll(".plt-btn")
        .forEach((b) => b.classList.toggle("active", b === btn));

      const select = toggle.querySelector(".plt-select");
      if (select) {
        select.value = platform;
      }

      codeBlock.innerHTML = highlightPython(CODE_SNIPPETS[snippet][platform]);
    });
  });

  const select = toggle.querySelector(".plt-select");
  if (select) {
    select.addEventListener("change", (e) => {
      const platform = e.target.value;
      const container = toggle.closest(".hero-code, .example-panel");
      const codeBlock = container.querySelector("code.code-python");
      const snippet = codeBlock.dataset.snippet;

      if (!CODE_SNIPPETS[snippet]?.[platform]) return;

      // Sync the buttons in case we switch back to desktop
      toggle
        .querySelectorAll(".plt-btn")
        .forEach((b) =>
          b.classList.toggle("active", b.dataset.platform === platform),
        );

      codeBlock.innerHTML = highlightPython(CODE_SNIPPETS[snippet][platform]);
    });
  }
});

// ── Mode toggle (feature/mode switcher inside any panel) ─────
document.querySelectorAll(".mode-toggle").forEach((toggle) => {
  const getActivePlatform = (container) => {
    const pToggle = container.querySelector(".platform-toggle");
    return (
      pToggle?.querySelector(".plt-btn.active")?.dataset.platform ||
      pToggle?.querySelector(".plt-select")?.value ||
      "telegram"
    );
  };

  const applyMode = (mode) => {
    const container = toggle.closest(".example-panel");
    const codeBlock = container.querySelector("code.code-python");
    // Each mode-btn carries its own data-snippet; fall back to mode value
    const activeBtn = toggle.querySelector(`.mode-btn[data-mode="${mode}"]`);
    const snippet = activeBtn?.dataset.snippet || mode;
    const platform = getActivePlatform(container);

    if (!CODE_SNIPPETS[snippet]?.[platform]) return;

    toggle
      .querySelectorAll(".mode-btn")
      .forEach((b) => b.classList.toggle("active", b.dataset.mode === mode));

    const modeSelect = toggle.querySelector(".mode-select");
    if (modeSelect) modeSelect.value = mode;

    codeBlock.dataset.snippet = snippet;
    codeBlock.innerHTML = highlightPython(CODE_SNIPPETS[snippet][platform]);
  };

  toggle.querySelectorAll(".mode-btn").forEach((btn) => {
    btn.addEventListener("click", () => applyMode(btn.dataset.mode));
  });

  const modeSelect = toggle.querySelector(".mode-select");
  if (modeSelect) {
    modeSelect.addEventListener("change", (e) => applyMode(e.target.value));
  }
});

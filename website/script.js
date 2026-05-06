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
  { threshold: 0.15 }
);

revealElements.forEach((element) => revealObserver.observe(element));

const tabs = document.querySelectorAll(".example-tab:not(.setup-tab)");
const panels = document.querySelectorAll(".example-panel:not(.setup-panel)");

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
      const idx = placeholders.push(`<span class="${tokenClass}">${match}</span>`) - 1;
      return `@@HL${idx}@@`;
    });
  };

  // Protect strings/comments from later substitutions.
  stash(/("""[\s\S]*?"""|'''[\s\S]*?'''|"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')/g, "tok-string");
  stash(/#.*/g, "tok-comment");

  code = code.replace(/(^\s*)(@[A-Za-z_][\w.]*)/gm, "$1<span class=\"tok-decorator\">$2</span>");
  code = code.replace(/\b(def|class)\s+([A-Za-z_][A-Za-z0-9_]*)\b/g, (m, kw, name) => {
    return `<span class="tok-keyword">${kw}</span> <span class="tok-function">${name}</span>`;
  });
  code = code.replace(/\b(from|import|as|if|elif|else|for|while|return|try|except|finally|with|in|pass|raise|break|continue|lambda|and|or|not|is|yield|await|async|global|nonlocal|assert|del)\b/g, "<span class=\"tok-keyword\">$1</span>");
  code = code.replace(/\b(True|False|None|self)\b/g, "<span class=\"tok-builtin\">$1</span>");
  code = code.replace(/\b\d+(?:\.\d+)?\b/g, "<span class=\"tok-number\">$&</span>");

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
    telegram:
`from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(token="123456:ABC-DEF...")
slackker = SimpleCallback(client)

@slackker.notifier
def train_model():
    return "done"

slackker.notify(event="training_complete", status="completed")`,
    slack:
`from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(token="xoxb-...", channel="A04AAB77ABC")
slackker = SimpleCallback(client)

@slackker.notifier
def train_model():
    return "done"

slackker.notify(event="training_complete", status="completed")`,
  teams:
`from slackker.core import TeamsClient
from slackker.callbacks.simple import SimpleCallback

client = TeamsClient(
  app_id="YOUR_AZURE_APP_ID",
  chat_id="19:abc@thread.v2",
  verbose=1
)
slackker = SimpleCallback(client)

@slackker.notifier
def train_model():
  return "done"

slackker.notify(event="training_complete", status="completed")`,
  },
  basic: {
    telegram:
`from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="123456:ABC-DEF...",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def run_data_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_data_pipeline("./data/train.csv")
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
    slack:
`from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel="A04AAB77ABC",
    verbose=1
)
notify = SimpleCallback(client)

@notify.notifier
def run_data_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

if __name__ == "__main__":
    rows, status = run_data_pipeline("./data/train.csv")
    notify.notify(
        event="pipeline_finished",
        rows_processed=rows,
        status=status,
        attachment="./artifacts/summary.txt"
    )`,
    teams:
  `from slackker.core import TeamsClient
  from slackker.callbacks.simple import SimpleCallback

  client = TeamsClient(
    app_id="YOUR_AZURE_APP_ID",
    chat_id="19:abc@thread.v2",
    verbose=1
  )
  notify = SimpleCallback(client)

  @notify.notifier
  def run_data_pipeline(source_path: str):
    rows_processed = 12500
    status = "success"
    return rows_processed, status

  if __name__ == "__main__":
    rows, status = run_data_pipeline("./data/train.csv")
    notify.notify(
      event="pipeline_finished",
      rows_processed=rows,
      status=status,
      attachment="./artifacts/summary.txt"
    )`,
  },
  keras: {
    telegram:
`from slackker.core import TelegramClient
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
    slack:
`from slackker.core import SlackClient
from slackker.callbacks.keras import KerasCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel="A04AAB77ABC",
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
  teams:
`from slackker.core import TeamsClient
from slackker.callbacks.keras import KerasCallback

client = TeamsClient(
  app_id="YOUR_AZURE_APP_ID",
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
  },
  lightning: {
    telegram:
`from lightning.pytorch import Trainer
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
    slack:
`from lightning.pytorch import Trainer
from slackker.core import SlackClient
from slackker.callbacks.lightning import LightningCallback

client = SlackClient(
    token="xoxb-your-bot-token",
    channel="A04AAB77ABC",
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
  teams:
`from lightning.pytorch import Trainer
from slackker.core import TeamsClient
from slackker.callbacks.lightning import LightningCallback

client = TeamsClient(
  app_id="YOUR_AZURE_APP_ID",
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

      toggle.querySelectorAll(".plt-btn").forEach((b) =>
        b.classList.toggle("active", b === btn)
      );

      codeBlock.innerHTML = highlightPython(CODE_SNIPPETS[snippet][platform]);
    });
  });
});

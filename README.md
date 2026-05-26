# Introducing slackker! :fire:

[![slackker-logo.png](https://i.postimg.cc/mgSDJPds/slackker-logo.png)](https://postimg.cc/RWN4nZ5s)
<div align="center">

![Tests](https://img.shields.io/github/actions/workflow/status/siddheshgunjal/slackker/pr-tests.yml?style=for-the-badge&logo=checkmarx&label=Tests)
![Python Build](https://img.shields.io/github/actions/workflow/status/siddheshgunjal/slackker/publish-to-pypi.yml?style=for-the-badge&logo=python&logoColor=yellow&label=Build)
[<img alt="Website" src="https://img.shields.io/website?url=https%3A%2F%2Fslackker.com&style=for-the-badge&logo=htmx">][website]
![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fsiddheshgunjal%2Fslackker%2Frefs%2Fheads%2Fmain%2Fpyproject.toml&style=for-the-badge)

</div>

<div align="center">

[<img alt="PyPI - Version" src="https://img.shields.io/pypi/v/slackker?style=for-the-badge&logo=python&logoColor=yellow&label=pip%20install%20slackker&color=teal" width="400">][py-pi]

</div>

`slackker` sends real-time notifications, custom updates, and metric plots from any Python script directly to **Slack, Telegram, Microsoft Teams, or Discord** — so you can step away from the screen and still stay informed. :coffee:

https://github.com/user-attachments/assets/41ab1ee9-4d3c-44d0-82b2-3194acbf7727

# Table of contents :notebook:
* [Installation](#installation-arrow_down)
* [Quick Start](#quick-start-rocket)
* [Create a Client](#create-a-client)
* [SimpleCallback — any Python function](#simplecallback--any-python-function)
* [Interactive Pipeline](#interactive-pipeline)
* [Keras](#use-with-keras)
* [Lightning](#use-with-lightning)
* [Legacy API (deprecated)](#legacy-api-deprecated)
* [Support](#support-sparkles)
* [Citation](#citation-page_facing_up)
* [Maintainer](#maintainer-sunglasses)

# Installation :arrow_down:
Install slackker from [UV][uv] (recommended) or pip. Requires `Python >= 3.10`.

```sh
uv add slackker
```
```sh
pip install slackker
```

# Quick Start :rocket:
```python
from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=1,
)
notify = SimpleCallback(client)

@notify.notifier
def train_model():
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train_model()
```

Refer to our [website](https://slackker.com/#setup) for platform setup instructions (Slack, Telegram, Teams, Discord).

# Create a Client
All slackker callbacks use a **client** object. Create one for your platform and pass it to any callback.

```python
from slackker.core import SlackClient, TelegramClient, TeamsClient, DiscordClient
```

```python
# Slack
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
    verbose=0,
)

# Telegram
client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=0,
)

# Microsoft Teams
client = TeamsClient(
    app_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    tenant_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    chat_id="19:xxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxxxxxxxxxxxx@thread.v2",
    verbose=0,
)

# Discord
client = DiscordClient(
    token="your_bot_token_here",
    channel_id="123456789012345678",
    verbose=0,
)
```

> **First-time Teams setup:** On the first run, `TeamsClient` prints a short URL and a code. Visit the URL, enter the code, and sign in. The token is then cached and silently refreshed on every subsequent run.

<details>
<summary><strong>Client parameters</strong></summary>

**Shared parameters (Slack, Telegram, Discord):**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | `str` | _required_ | Slack app / Telegram bot / Discord bot token |
| `channel` | `str` | _required (Slack only)_ | Slack channel ID |
| `channel_id` | `str` | _required (Discord only)_ | Discord channel ID |
| `chat_id` | `str` | `None` _(Telegram only)_ | Telegram chat ID — auto-discovered if omitted |
| `verbose` | `int` | `0` | `0` = silent, `1` = info, `2` = debug |

**Teams-specific parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` | _required_ | Azure AD application (client) ID |
| `tenant_id` | `str` | `"common"` | Azure AD tenant ID, or `"common"` for personal + org accounts |
| `chat_id` | `str` | _required_ | Teams chat ID (e.g. `19:..._...@thread.v2`) — right-click a message → Copy link, extract from URL |
| `token_cache_path` | `str` | `~/.slackker/teams_<app_id[:8]>.json` | Path to cache the access/refresh token |
| `verbose` | `int` | `0` | `0` = silent, `1` = info, `2` = debug |

</details>

# SimpleCallback — any Python function
![python-banner](https://brandslogos.com/wp-content/uploads/images/large/python-logo-1.png)

```python
from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=1,
)
notify = SimpleCallback(client)

# Decorator — automatically sends function name, execution time, and return value
@notify.notifier
def train():
    # ... your training code ...
    return {"accuracy": 0.94, "loss": 0.12}

train()

# notify() — send a custom update anywhere, with optional file attachment
notify.notify(
    event="training_complete",
    attachment="./artifacts/model.ckpt",
    best_val_loss=0.0123,
    epoch=20,
)
```

> Works with any client: `SlackClient`, `TelegramClient`, `TeamsClient`, or `DiscordClient`.

**Async:** use `await notify.async_notify(event="step_done", accuracy=0.95)` in async contexts.

<details>
<summary><strong>SimpleCallback parameters</strong></summary>

**Constructor:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `client` | `BaseClient` | A slackker client instance |

**`notify()` / `async_notify()` parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `event` | `str` | `None` | Label in the notification header; defaults to script filename |
| `attachment` | `str` | `None` | Path to a file to send alongside the notification |
| `**kwargs` | — | — | Any key-value pairs to include in the notification body |

**`ask()` / `async_ask()` parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `question` | `str` | _required_ | Message sent to the platform asking for a reply |
| `timeout` | `float` | `60.0` | Seconds to wait for a reply; auto-continues on timeout |
| `halt_on` | `str` | `"no"` | Reply text (case-insensitive) that halts the flow |

Returns `True` to continue, `False` to halt.

</details>

# Interactive Pipeline

Use `ask()` to send a message and wait for the user's reply — ideal for checkpoints, confirmations, or human-in-the-loop pipelines:

```python
from slackker.core import TelegramClient
from slackker.callbacks.simple import SimpleCallback

client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=1,
)
notifier = SimpleCallback(client)

def pipeline():
    notifier.notify(event="preprocessing_done", samples=10000)

    reply = notifier.ask("Preprocessing done. Start training? (yes/no)")
    if reply.lower() != "yes":
        return

    # ... training ...
    notifier.notify(event="training_complete", accuracy=0.94)

pipeline()
```

**Async version:** use `await notifier.async_ask("...")` in async contexts.

# Use with [Keras][keras]
![keras-banner](https://i.postimg.cc/MpLBBTn7/slackker-keras.png)

```python
from slackker.core import TelegramClient
from slackker.callbacks.keras import KerasCallback

client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=1,
)
slackker = KerasCallback(
    client=client,
    model_name="MyModel",
    export="png",
    send_plot=True,
)

history = model.fit(
    x_train, y_train,
    epochs=10,
    batch_size=32,
    validation_data=(x_val, y_val),
    callbacks=[slackker],
)
```

> Works with any client: `SlackClient`, `TelegramClient`, `TeamsClient`, or `DiscordClient`.

<details>
<summary><strong>KerasCallback parameters</strong></summary>

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `BaseClient` | _required_ | A slackker client instance |
| `model_name` | `str` | _required_ | Name used in messages and plot titles |
| `export` | `str` | `"png"` | Plot format _(eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_ |
| `send_plot` | `bool` | `False` | Send training/validation plots when training ends |

</details>

# Use with [Lightning][lightning]
![lightning-banner](https://i.postimg.cc/fR5Nqtcd/slackker-lightning.png)

Unlike Keras, Lightning requires you to explicitly log metrics using `self.log()` inside your `LightningModule`. Use `on_epoch=True` in `training_step` so slackker can read them at the end of each epoch.

```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision as tv
import torch.nn.functional as F
from lightning.pytorch import LightningModule, Trainer

from slackker.core import TelegramClient
from slackker.callbacks.lightning import LightningCallback


class LightningModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(28 * 28, 256)
        self.fc2 = nn.Linear(256, 128)
        self.out = nn.Linear(128, 10)

    def forward(self, x):
        batch_size, _, _, _ = x.size()
        x = x.view(batch_size, -1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)

    def configure_optimizers(self):
        return torch.optim.Adam(self.parameters(), lr=1e-3)

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        accuracy = (torch.max(y_hat, 1)[1] == y).float().mean()
        # log with on_epoch=True so slackker can read them at epoch end
        self.log("train_loss", loss, on_epoch=True)
        self.log("train_acc", accuracy, on_epoch=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        accuracy = (torch.max(y_hat, 1)[1] == y).float().mean()
        # on_epoch=True by default in validation_step
        self.log("val_loss", loss)
        self.log("val_acc", accuracy)
        return loss


train_data = tv.datasets.MNIST(".", train=True, download=True, transform=tv.transforms.ToTensor())
val_data = tv.datasets.MNIST(".", train=False, download=True, transform=tv.transforms.ToTensor())
train_loader = DataLoader(train_data, batch_size=128)
val_loader = DataLoader(val_data, batch_size=128)

model = LightningModel()

client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=1,
)
slackker = LightningCallback(
    client=client,
    model_name="MyModel",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)

trainer = Trainer(max_epochs=10, callbacks=[slackker])
trainer.fit(model, train_loader, val_loader)
```

> Works with any client: `SlackClient`, `TelegramClient`, `TeamsClient`, or `DiscordClient`.

<details>
<summary><strong>LightningCallback parameters</strong></summary>

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `BaseClient` | _required_ | A slackker client instance |
| `model_name` | `str` | _required_ | Name used in messages and plot titles |
| `track_logs` | `list[str]` | _required_ | Metrics to track and report each epoch |
| `monitor` | `str` | `None` | Metric used to determine the best epoch |
| `export` | `str` | `"png"` | Plot format _(eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_ |
| `send_plot` | `bool` | `False` | Send training plots when training ends |

</details>

---

# Legacy API (deprecated)

> **Note:** The old `Update`, `SlackUpdate`, and `TelegramUpdate` classes still work but emit a `DeprecationWarning`. They will be removed in a future release. Please migrate to `SimpleCallback` and the new client-based API shown above.

<details>
<summary><strong>Click to expand legacy usage examples</strong></summary>

### Basic callbacks (legacy)
```python
from slackker.callbacks.basic import SlackUpdate   # or TelegramUpdate

# Slack
slackker = SlackUpdate(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

# Telegram
slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG")

@slackker.notifier
def your_function():
    return value_1, value_2

slackker.notify(event="done", value_1=value_1)
```

### Keras callbacks (legacy)
```python
from slackker.callbacks.keras import SlackUpdate   # or TelegramUpdate

slackker = SlackUpdate(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
    ModelName="Keras_NN",
    export="png",
    SendPlot=True,
)

history = model.fit(..., callbacks=[slackker])
```

### Lightning callbacks (legacy)
```python
from slackker.callbacks.lightning import SlackUpdate   # or TelegramUpdate

slackker = SlackUpdate(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
    ModelName="Lightning NN",
    TrackLogs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    SendPlot=True,
)

trainer = Trainer(max_epochs=2, callbacks=[slackker])
trainer.fit(model, train_loader, test_loader)
```

</details>

#  Support :sparkles:
If you get stuck, we’re here to help. The following are the best ways to get assistance working through your issue:

* Use our [Github Issue Tracker][gh-issues] for reporting bugs or requesting features.
Contribution are the best way to keep `slackker` amazing :muscle:
* If you want to contribute please refer [Contributor's Guide][gh-contrib] for how to contribute in a helpful and collaborative way :innocent:

# Citation :page_facing_up:
Please cite slackker in your publications if this is useful for your project/research. Here is an example BibTeX entry:
```BibTeX
@misc{siddheshgunjal2023slackker,
  title={slackker},
  author={Siddhesh Gunjal},
  year={2023},
  howpublished={\url{https://github.com/siddheshgunjal/slackker}},
}
```

# Maintainer :sunglasses:
[<img alt="Static Badge" src="https://img.shields.io/badge/my_website-click_to_visit-informational?style=for-the-badge&logo=googlechrome&logoColor=white&color=black">][portfolio]

<!-- Markdown link -->
[license]: https://github.com/siddheshgunjal/slackker/blob/main/LICENSE
[keras]: https://keras.io/
[lightning]: https://lightning.ai/
[setup-slack]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-to-monitor-keras-model-training-status-on-slack-9f67265dfabd
[setup-telegram]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-with-telegram-to-monitor-keras-model-training-21b1ff0c1020
[keras]: https://github.com/keras-team/keras
[py-pi]: https://pypi.org/project/slackker/
[slack-app]: https://api.slack.com/apps
[gh-issues]: https://github.com/siddheshgunjal/slackker/issues
[gh-contrib]: https://github.com/siddheshgunjal/slackker/blob/main/CONTRIBUTING.md
[portfolio]: https://siddheshgunjal.github.io
[GitHub]: https://github.com/siddheshgunjal
[website]: https://slackker.com
[uv]: https://docs.astral.sh/uv/

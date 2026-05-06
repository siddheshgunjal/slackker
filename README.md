# Introducing slackker! :fire:

[![slackker-logo.png](https://i.postimg.cc/mgSDJPds/slackker-logo.png)](https://postimg.cc/RWN4nZ5s)
<div align="center">

![Tests](https://img.shields.io/github/actions/workflow/status/siddheshgunjal/slackker/pr-tests.yml?style=for-the-badge&logo=checkmarx&label=Tests)
![Python Build](https://img.shields.io/github/actions/workflow/status/siddheshgunjal/slackker/publish-to-pypi.yml?style=for-the-badge&logo=python&logoColor=yellow&label=Build)
[<img alt="Website" src="https://img.shields.io/website?url=https%3A%2F%2Fslackker.com&style=for-the-badge&logo=htmx">][website]

</div>

<div align="center">

[<img alt="PyPI - Version" src="https://img.shields.io/pypi/v/slackker?style=for-the-badge&logo=python&logoColor=yellow&label=pip%20install%20slackker&color=teal" width="400">][py-pi]

</div>

Watching training metrics is a time killer and addictive. Have you ever found yourself walking back and forth to computer to monitor progress, only to find that the current epoch is not finished yet or that nothing has changed?

When you're in front of your screen, you start to look for patterns in the metrics to judge the progress, this way training spills over into the rest of your live. All the time the models are training, your brain works at 50% at most. So, I made slackker to make your life easy :grin:

`slackker` provides a simple and flexible way to send notifications, updates, and even plots of your training metrics directly to your preferred messaging platform. Whether you're training a deep learning model or running a long-running script, slackker keeps you informed without the need to constantly check your terminal.
Features:
* **Integrate within any _.py_ function/script**: You can integrate slackker with any pipeline built in python
* **Real-time updates**: Get updates on your progress in real-time on Slack & Telegram.
* **Exported Plots**: Exported plots of training metrics and send it to your Slack channel.
* **Customizable**: Customize the metrics you want to track and notify.
* **Easy to use**: Just import the package, setup the slack/telegram and you are good to go.

So now you don't have to sit in front of the machine all the time. You can quickly go and grab coffee :coffee: downstairs or run some errands and still keep tracking the progress while on the move without loosing your peace of mind.

# Table of contents :notebook:
* [Installation](#installation-arrow_down)
* [Getting started with slackker callbacks](#getting-started-with-slackker-callbacks)
  * [Setup slackker](#setup-slackker)
  * [Create a Client](#create-a-client)
  * [Use slackker callbacks for any python functions](#use-slackker-callbacks-for-any-python-functions)
  * [Use slackker callbacks with Keras](#use-slackker-callbacks-with-keras)
  * [Use slackker callbacks with Lightning](#use-slackker-callbacks-with-lightning)
* [Legacy API (deprecated)](#legacy-api-deprecated)
* [Support](#support-sparkles)
* [Citation](#citation-page_facing_up)
* [Maintainer](#maintainer-sunglasses)

# Installation :arrow_down:
* Install slackker from [UV][uv] is recommended. slackker is compatible with `Python >= 3.11` and runs on Linux, MacOS X and Windows. 
* Installing slackker in your environment is easy. Just use below command:

```sh
uv add slackker
```

OR
```sh
pip install slackker
```

# Getting started with slackker callbacks
## Setup slackker
Refer to our [website](https://slackker.com/#setup) for detailed setup instructions with Slack, Telegram, and Microsoft Teams

## Create a Client
All slackker callbacks now use a **client** object. Create one for your platform first, then pass it to any callback.

```python
from slackker.core import SlackClient, TelegramClient, TeamsClient
```

### Slack
```python
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
    verbose=0,
)
```

### Telegram
```python
client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    verbose=0,
)
```

### Microsoft Teams
```python
client = TeamsClient(
    app_id="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
    chat_id="19:xxxxxxxxxxxxxxxxxxxxxx_xxxxxxxxxxxxxxxxxxxxxx@unq.gbl.spaces",
    verbose=0,
)
```

> **First-time setup:** On the first run, `TeamsClient` prints a short URL and a code. Visit the URL in any browser, enter the code, and sign in with your Microsoft account. The token is then cached at `~/.slackker/teams_<app_id[:8]>.json` and silently refreshed on every subsequent run — no login prompt after the first time.

**Parameters (shared):**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `token` | `str` | _required_ | Slack app / Telegram bot token |
| `channel` | `str` | _required (Slack only)_ | Slack channel ID to receive updates |
| `chat_id` | `str` | `None` _(Telegram only)_ | Telegram chat ID. Auto-discovered if omitted |
| `verbose` | `int` | `0` | `0` = no logging, `1` = info, `2` = debug |

**Teams-specific parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `app_id` | `str` | _required_ | Azure AD application (client) ID from your app registration |
| `tenant_id` | `str` | `"common"` | Azure AD tenant ID, or `"common"` to accept personal and organisational accounts |
| `chat_id` | `str` | _required_ | Teams personal chat ID (e.g. `19:..._...@unq.gbl.spaces`). Find via Graph Explorer: `GET /me/chats` |
| `token_cache_path` | `str` | `~/.slackker/teams_<app_id[:8]>.json` | Path to cache the access/refresh token |
| `verbose` | `int` | `0` | `0` = no logging, `1` = info, `2` = debug |

## Use slackker callbacks for any python functions
![python-banner](https://brandslogos.com/wp-content/uploads/images/large/python-logo-1.png)

### Import
```python
from slackker.core import SlackClient          # or TelegramClient, TeamsClient
from slackker.callbacks.simple import SimpleCallback
```

### Create the SimpleCallback object
```python
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

slackker = SimpleCallback(client)
```

### Wrap your function with the `notifier` decorator
```python
@slackker.notifier
def your_function():
    return value_1, value_2
```
The following message will be sent to your channel when the function executes:
```text
Function 'your_function' from Script: 'your_script.py' executed.
Execution time: 5.006 Seconds
Returned 2 outputs:
Output 0:
value_1

Output 1:
value_2
```

### Send a notification with `notify()`
You can also use `slackker.notify()` anywhere in your script to send a custom notification:
```python
slackker.notify(
    event="training_complete",
    value_1=arg1,
    value_2=f"This is argument 2 = {arg2}",
    status="completed",
)
```
The following message will be sent:
```text
Notification: training_complete at 14-10-2024 12:15:54

value_1: arg1
value_2: This is argument 2 = arg2
status: completed
```

To send a file with the notification, pass the file path using `attachment`:
```python
slackker.notify(
    event="training_complete",
    attachment="./artifacts/model.ckpt",
    best_val_loss=0.0123,
    epoch=20,
)
```

### Async support
If you are working in an async context, use `async_notify()` directly:
```python
await slackker.async_notify(event="step_done", accuracy=0.95)
```

### Final code for python function
```python
from slackker.core import SlackClient
from slackker.callbacks.simple import SimpleCallback

# Create client & SimpleCallback object
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)
slackker = SimpleCallback(client)

@slackker.notifier
def your_function():
    return value_1, value_2

your_function()

slackker.notify(
    event="script_finished",
    attachment="./artifacts/summary.txt",
    value_1=value_1,
    value_2=value_2,
)
```

## Use slackker callbacks with [Keras][keras]
![keras-banner](https://i.postimg.cc/MpLBBTn7/slackker-keras.png)

### Import slackker for Keras
```python
from slackker.core import SlackClient          # or TelegramClient, TeamsClient
from slackker.callbacks.keras import KerasCallback
```

### Create KerasCallback object
```python
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

slackker = KerasCallback(
    client=client,
    model_name="Keras_NN",
    export="png",
    send_plot=True,
)
```
or with Telegram:
```python
client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
)

slackker = KerasCallback(
    client=client,
    model_name="Simple_NN",
    export="png",
    send_plot=True,
)
```

**KerasCallback Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `BaseClient` | _required_ | A `SlackClient` or `TelegramClient` instance |
| `model_name` | `str` | _required_ | Name of your model (used in messages & plot titles) |
| `export` | `str` | `"png"` | Plot export format _(eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_ |
| `send_plot` | `bool` | `False` | If `True`, sends training/validation plots when training ends |

### Call slackker object in model.fit()
```python
history = model.fit(
    x_train, y_train,
    epochs=3,
    batch_size=16,
    verbose=1,
    validation_data=(x_val, y_val),
    callbacks=[slackker],
)
```

### Final code for Keras
```python
from slackker.core import SlackClient
from slackker.callbacks.keras import KerasCallback

# Train-Test split
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size=0.8)

# Build keras model
model = Sequential()
model.add(Dense(8, activation='relu', input_shape=(IMG_WIDTH, IMG_HEIGHT, DEPTH)))
model.add(Dense(3, activation='softmax'))
model.compile(optimizer='rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

# Create Client & KerasCallback
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

slackker = KerasCallback(
    client=client,
    model_name="SampleModel",
    export="png",
    send_plot=True,
)

# Pass slackker to model.fit() callbacks
history = model.fit(
    x_train, y_train,
    epochs=3,
    batch_size=16,
    verbose=1,
    validation_data=(x_val, y_val),
    callbacks=[slackker],
)
```

## Use slackker callbacks with [Lightning][lightning]
![lightning-banner](https://i.postimg.cc/fR5Nqtcd/slackker-lightning.png)

### Import slackker for Lightning
```python
from slackker.core import SlackClient          # or TelegramClient, TeamsClient
from slackker.callbacks.lightning import LightningCallback
```

### Log your metrics to track
#### Log Training loop metrics
```python
self.log("train_loss", loss, on_epoch=True)
self.log("train_acc", accuracy, on_epoch=True)
```
Make sure to set `on_epoch=True` in the training step.

#### Log Validation loop metrics
```python
self.log("val_loss", loss)
self.log("val_acc", accuracy)
```
In the validation step `on_epoch=True` by default.

### Create LightningCallback object
```python
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

slackker = LightningCallback(
    client=client,
    model_name="Lightning NN",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)
```
or with Telegram:
```python
client = TelegramClient(
    token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
)

slackker = LightningCallback(
    client=client,
    model_name="Lightning NN",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)
```

**LightningCallback Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `client` | `BaseClient` | _required_ | A `SlackClient` or `TelegramClient` instance |
| `model_name` | `str` | _required_ | Name of your model (used in messages & plot titles) |
| `track_logs` | `list[str]` | _required_ | List of metrics to track & report each epoch |
| `monitor` | `str` | `None` | Metric used to determine the best epoch |
| `export` | `str` | `"png"` | Plot export format _(eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_ |
| `send_plot` | `bool` | `False` | If `True`, sends training plots when training ends |

### Call slackker object in Trainer module
```python
trainer = Trainer(max_epochs=2, callbacks=[slackker])
```

### Final code for Lightning
```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision as tv
import torch.nn.functional as F
from lightning.pytorch import LightningModule, Trainer
from lightning.pytorch.callbacks import ModelCheckpoint

from slackker.core import SlackClient
from slackker.callbacks.lightning import LightningCallback

class LightningModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(28*28, 256)
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
        _, predictions = torch.max(y_hat, dim=1)
        accuracy = torch.sum(predictions == y) / y.shape[0]
        self.log("train_loss", loss, on_epoch=True)
        self.log("train_acc", accuracy, on_epoch=True)
        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)
        loss = F.cross_entropy(y_hat, y)
        _, predictions = torch.max(y_hat, dim=1)
        accuracy = torch.sum(predictions == y) / y.shape[0]
        self.log("val_loss", loss)
        self.log("val_acc", accuracy)
        return loss

train_data = tv.datasets.MNIST(".", train=True, download=True, transform=tv.transforms.ToTensor())
test_data = tv.datasets.MNIST(".", train=False, download=True, transform=tv.transforms.ToTensor())
train_loader = DataLoader(train_data, batch_size=128)
test_loader = DataLoader(test_data, batch_size=128)

model = LightningModel()

# Create Client & LightningCallback
client = SlackClient(
    token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="C04AAB77ABC",
)

slackker = LightningCallback(
    client=client,
    model_name="Lightning NN",
    track_logs=["train_loss", "train_acc", "val_loss", "val_acc"],
    monitor="val_loss",
    export="png",
    send_plot=True,
)

trainer = Trainer(max_epochs=2, callbacks=[slackker])
trainer.fit(model, train_loader, test_loader)
```

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
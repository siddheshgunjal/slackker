# Introducing slackker! :fire:

[![slackker-logo.png](https://i.postimg.cc/mgSDJPds/slackker-logo.png)](https://postimg.cc/RWN4nZ5s)

Watching training metrics is a time killer and addictive. Have you ever found yourself walking back and forth to computer to monitor progress, only to find that the current epoch is not finished yet or that nothing has changed?

When you're in front of your screen, you start to look for patterns in the metrics to judge the progress, this way training spills over into the rest of your live. All the time the models are training, your brain works at 50% at most. So, I made slackker to make your life easy :grin:

<div align="center">

[<img alt="PyPI - Version" src="https://img.shields.io/pypi/v/slackker?style=for-the-badge&logo=python&logoColor=yellow&label=pip%20install%20slackker&color=teal" width="400">][py-pi]

_Requirements: `slack_sdk>=3.19.0` and `matplotlib`_

</div>

`slackker` is a python package for monitoring your python script & ML model training status in real-time on Slack & Telegram.
Features:
* **Integrate within any _.py_ function/script**: You can integrate slackker with any python script or function.
* **Real-time updates**: Get updates on your training progress in real-time on Slack & Telegram.
* **Exported Plots**: Exported plots of training metrics and send it to your Slack channel.
* **Customizable**: Customize the metrics you want to track and notify.
* **Easy to use**: Just import the package, setup the slack/telegram and you are good to go.

So now you don't have to sit in front of the machine all the time. You can quickly go and grab coffee :coffee: downstairs or run some errands and still keep tracking the progress while on the move without loosing your peace of mind.

# Table of contents :notebook:
* [Installation](#installation-arrow_down)
* [Getting started with slackker callbacks](#getting-started-with-slackker-callbacks)
  * [Setup slackker](#setup-slackker)
  * [Use slackker callbacks for any python functions](#use-slackker-callbacks-for-any-python-functions)
  * [Use slackker callbacks with Keras](#use-slackker-callbacks-with-keras)
  * [Use slackker callbacks with Lightning](#use-slackker-callbacks-with-lightning)
* [Support](#support-sparkles)
* [Citation](#citation-page_facing_up)
* [Maintainer](#maintainer-sunglasses)

# Installation :arrow_down:
* Install slackker from [PyPi][py-pi] is recommended. slackker is compatible with `Python >= 3.6` and runs on Linux, MacOS X and Windows. 
* Installing slackker in your environment is easy. Just use below pip command:

```bash
pip install slackker
```

# Getting started with slackker callbacks
## Setup slackker
* Slack: [How to setup slackker for your slack channel][setup-slack]
* Telegram: [How to setup slackker for Telegram][setup-telegram]

## Use slackker callbacks for any python functions
![python-banner](https://brandslogos.com/wp-content/uploads/images/large/python-logo-1.png)
Import basic slackker callbacks with following line:
```python
from slackker.callbacks.basic import SlackUpdate # for slack
###################### OR ######################
from slackker.callbacks.basic import TelegramUpdate # for telegram
```
Create slackker object.
```python
# for Slack
slackker = SlackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC")
```
or
```python
# for Telegram
slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG")
```
* `token`: _(string)_ Slack app/Telegram token
* `channel`: _(string)_ Slack channel where you want to receive updates
* `verbose`: _(int)_ default `0`: You can sent the verbose level up to 3.
  * `verbose = 0` No logging
  * `verbose = 1` Info logging
  * `verbose = 2` Debug/In-depth logging

Now you can wrap your function with this slackker object.
```python
@slackker.notifier
def your_function():
    return value_1, value_2
```
following messages will be sent to your slack channel when the function executes.

```text
Function 'your_function' from Script: 'your_script.py' executed.
Execution time: 5.006 Seconds
Returned 2 outputs:
Output 0:
value_1

Output 1:
value_2
```

You can also use `slackker.notify(*args, **kwargs)` at the end of your script to notify the end of script execution.
```python
if __name__ == "__main__":
    your_function()
    slackker.notify(arg1, f"This is argument 2 = {arg2}", value="This is a string") 
```
following message will be sent to your slack channel when the script ends.
```text
Your script: 'your_script.py' has been executed successfully at 14-10-2024 12:15:54

arg1

This is argument 2 = arg2

value: This is a string
```
### Final code for python function
```python
from slackker.callbacks.basic import SlackUpdate
###################### OR ######################
from slackker.callbacks.basic import TelegramUpdate # for telegram

# for Slack
slackker = SlackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC")
###################### OR ######################
# for Telegram
slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG")

@slackker.notifier
def your_function():
    return value_1, value_2

slackker.notify(f"This is value 1: {value_1}", value=value_2)
```
## Use slackker callbacks with [Keras][keras]
![keras-banner](https://i.postimg.cc/MpLBBTn7/slackker-keras.png)
### Import slackker for Keras
Import slackker callbacks for keras with following line:
```python
from slackker.callbacks.keras import SlackUpdate # for slack
###################### OR ######################
from slackker.callbacks.keras import TelegramUpdate # for telegram
```
### Create slackker object for keras
Create slackker object.
```python
# for Slack
slackker = SlackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC",
    ModelName='Keras_NN',
    export='png',
    SendPlot=True)
```
or
```python
# for Telegram
slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    ModelName='Simple_NN',
    export='png',
    SendPlot=True)
```
* `token`: _(string)_ Slack app/Telegram token
* `channel`: _(string)_ Slack channel where you want to receive updates
* `ModelName`: _(string)_ Name for your model. This same name will be used in future for title of the generated plots.
* `export`: _(string)_ default `"png"`: Format for plots to be exported. _(supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_
* `SendPlots`: _(Bool)_ default `False`: If set to `True` it will export history of model, both training and validation, save it in the format given in `export` argument and send graphs to slack channel when training ends. If set to `False` it will not send exported graphs to slack channel. 
* `verbose`: _(int)_ default `0`: You can sent the verbose level up to 3.
  * `verbose = 0` No logging
  * `verbose = 1` Info logging
  * `verbose = 2` Debug/In-depth logging

### Call slackker object into model.fit()

Now you can call slackker object into callbacks argument just like any other callbacks object.
```python
history = model.fit(x_train, 
                    y_train,
                    epochs = 3,
                    batch_size = 16,
                    verbose=1,
                    validation_data=(x_val,y_val),
                    callbacks=[slackker])
```

### Final code for Keras
```python
# Import library for keras
from slackker.callbacks.keras import slackUpdate

# Train-Test split for your keras model
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size=0.8)

# Build keras model
model = Sequential()
model.add(Dense(8,activation='relu',input_shape = (IMG_WIDTH, IMG_HEIGHT, DEPTH)))
model.add(Dense(3,activation='softmax'))
model.compile(optimizer = 'rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

# Create Slackker object
slackker = slackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed48499bb",
    channel="A04AAB77ABC",
    modelName='SampleModel',
    export='png',
    sendPlot=True)

# Call Slackker object in model.fit() callbacks
history = model.fit(x_train, 
                    y_train,
                    epochs = 3,
                    batch_size = 16,
                    verbose=1,
                    validation_data=(x_val,y_val),
                    callbacks=[slackker])
```
## Use slackker callbacks with [Lightning][lightning]
![lightning-banner](https://i.postimg.cc/fR5Nqtcd/slackker-lightning.png)
### Import slackker for Lightning
Import slackker callbacks for PyTorch Lightning with following line:
```python
from slackker.callbacks.lightning import SlackUpdate # for slack
###################### OR ######################
from slackker.callbacks.lightning import TelegramUpdate # for telegram
```
### Log your metrics to track
#### Log Training loop metrics
```python
self.log("train_loss", loss, on_epoch=True)
self.log("train_acc", accuracy, on_epoch=True)
```
Make sure to set `on_epoch=True` to in training step.
#### Log Validation loop metrics
```python
self.log("val_loss", loss)
self.log("val_acc", accuracy)
```
In Validation step `on_epoch=True` by default.

### Create slackker object for lightning
```python
# for Slack
slackker = SlackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC",
    ModelName='Lightning NN',
    TrackLogs=['train_loss', 'train_acc', 'val_loss', 'val_acc'],
    monitor="val_loss",
    export='png',
    SendPlot=True)
```
or
```python
# for Telegram
slackker = TelegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    ModelName="Lightning NN Testing",
    TrackLogs=['train_loss', 'train_acc', 'val_loss', 'val_acc'],
    monitor="val_loss",
    export='png',
    SendPlot=True)
```
* `token`: _(string)_ Slack app/Telegram token
* `channel`: _(string)_ Slack channel where you want to receive updates
* `ModelName`: _(string)_ Name for your model. This same name will be used in future for title of the generated plots.
* `TrackLogs`: _(list)_ List of metrics you want slackker to track & notify.
* `monitor`: _(string)_ This metric will be used to determine best Epoch
* `export`: _(string)_ default `"png"`: Format for plots to be exported. _(supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)_
* `SendPlots`: _(Bool)_ default `False`: If set to `True` it will export history of model, both training and validation, save it in the format given in `export` argument and send graphs to slack channel when training ends. If set to `False` it will not send exported graphs to slack channel. 
* `verbose`: _(int)_ default `0`: You can sent the verbose level up to 3.
  * `verbose = 0` No logging
  * `verbose = 1` Info logging
  * `verbose = 2` Debug/In-depth logging

### Call slackker object in Trainer module
Now you can call slackker object into callbacks argument just like any other callbacks object.
```python
trainer = Trainer(max_epochs=2,callbacks=[slackker])
```

### Final code for Lightning
```python
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision as tv
import torch.nn.functional as F
from lightning.pytorch import LightningModule, Trainer
from lightning.pytorch.callbacks import ModelCheckpoint, Callback
from lightning.pytorch.loggers import CSVLogger

from slackker.callbacks.lightning import SlackUpdate
from slackker.callbacks.lightning import TelegramUpdate

class LightningModel(LightningModule):
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(28*28,256)
        self.fc2 = nn.Linear(256,128)
        self.out = nn.Linear(128,10)

    def forward(self, x):
        batch_size, _, _, _ = x.size()
        x = x.view(batch_size,-1)
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return self.out(x)

    def configure_optimizers(self):
        optimizer = torch.optim.Adam(self.parameters(), lr=1e-3)
        return optimizer

    def training_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)

        # calculate Loss
        loss = F.cross_entropy(y_hat,y)

        #calculate accuracy
        _, predictions = torch.max(y_hat, dim=1)
        correct_predictions = torch.sum(predictions == y)
        accuracy = correct_predictions / y.shape[0]

        self.log("train_loss", loss, on_epoch=True)
        self.log("train_acc", accuracy, on_epoch=True)

        return loss

    def validation_step(self, batch, batch_idx):
        x, y = batch
        y_hat = self.forward(x)

        # calculate Loss
        loss = F.cross_entropy(y_hat,y)

        #calculate accuracy
        _, predictions = torch.max(y_hat, dim=1)
        correct_predictions = torch.sum(predictions == y)
        accuracy = correct_predictions / y.shape[0]

        self.log("val_loss", loss)
        self.log("val_acc", accuracy)

        return loss

train_data = tv.datasets.MNIST(".", train=True, download=True, transform=tv.transforms.ToTensor())
test_data = tv.datasets.MNIST(".", train=False, download=True, transform=tv.transforms.ToTensor())
train_loader = DataLoader(train_data, batch_size=128)
test_loader = DataLoader(test_data, batch_size=128)

model = LightningModel()

# slackker checkpoint for slack
slackker = SlackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC",
    ModelName='Lightning NN',
    TrackLogs=['train_loss', 'train_acc', 'val_loss', 'val_acc'],
    monitor="val_loss",
    export='png',
    SendPlot=True)

trainer = Trainer(max_epochs=2, callbacks=[slackker])
trainer.fit(model, train_loader, test_loader)
```

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
[slack-sdk]: https://github.com/slackapi/python-slack-sdk
[license]: https://github.com/siddheshgunjal/slackker/blob/main/LICENSE
[keras]: https://keras.io/
[lightning]: https://lightning.ai/
[setup-slack]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-to-monitor-keras-model-training-status-on-slack-9f67265dfabd
[setup-telegram]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-with-telegram-to-monitor-keras-model-training-21b1ff0c1020
[matplot-lib]: https://github.com/matplotlib/matplotlib
[keras]: https://github.com/keras-team/keras
[py-pi]: https://pypi.org/project/slackker/
[slack-app]: https://api.slack.com/apps
[gh-issues]: https://github.com/siddheshgunjal/slackker/issues
[gh-contrib]: https://github.com/siddheshgunjal/slackker/blob/main/CONTRIBUTING.md
[portfolio]: https://siddheshgunjal.github.io
[GitHub]: https://github.com/siddheshgunjal
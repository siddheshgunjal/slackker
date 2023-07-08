# Introducing slackker! :fire:

![PyPI](https://img.shields.io/pypi/v/slackker?color=blue&label=pip) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/slackker?color=orange) ![PyPI - License](https://img.shields.io/pypi/l/slackker?color=gr)


`slackker` is a python package for monitoring your Keras training status in real-time on Slack & Telegram. It can send you update for your ML model training progress and send final report with graphs when the training finishes. So now you don't have to sit in front of the machine all the time. You can quickly go and grab coffee :coffee: downstairs or run some errands and still keep tracking the progress while on the move without loosing your peace of mind.

## Table of contents :notebook:

* [Requirements](#requirements-clipboard)
* [Installation](#installation-arrow_down)
* [Getting started with slackker callbacks](#getting-started-with-slackker-callbacks)
  * [Setup Slack to work with slackker](#setup-slack-to-work-with-slackker)
  * [Setup Telegram to work with slackker](#setup-slack-to-work-with-slackker)
  * [Using slackker callbacks with keras callbacks](#using-slackker-callbacks-with-keras-callbacks-method)
  * [Create slackker object for Slack](#create-slackker-object-for-slack)
  * [Create slackker object for Telegram](#create-slackker-object-for-telegram)
  * [Call slackker object into callbacks during model.fit()](#call-slackker-object-into-callbacks-during-model-fit)
  * [Final code](#final-code)
* [Support](#support-sparkles)
* [Citation](#citation-page_facing_up)
* [Maintainer](#maintainer-sunglasses)


## Requirements :clipboard:

* `slackker` utilises [slack_sdk][slack-sdk]`>=3.19.0` for communicating with slack API.
* To use the `slackker.callbacks.keras` [keras][keras]`>=2.0.0` is required.


## Installation :arrow_down:
* Install slackker from [PyPi][py-pi] is recommended. slackker is compatible with `Python >= 3.6` and runs on Linux, MacOS X and Windows. 
* Installing slackker in your environment is easy. Just use below pip command:

```bash
pip install slackker
```

## Getting started with slackker callbacks
### Setup Slack to work with slackker
* First create an [slack app][slack-app] from scratch in your workspace.
* we must give below mentioned permissions for `slackker` to be able to send status update and report to your channel:
  * `chat:write`
  * `chat:write.public`
  * `files:read`
  * `files:write`
* Now install the app to your workspace and copy our apps **Bot & OAuth Token**. It should be in following format:
```
 xoxb-123234234235-123234234235-adedce74748c3844747aed48499bb
```
* For detailed step by step guide, visit this article: [How to setup Slackker with Slack][setup-slack]
* Now go to slack and add this slack app to the channel where you wish to receive al the update. Now we are ready to use `slackker` in your training flow!:smiling_imp:

### Setup Telegram to work with slackker
* Open your telegram app and search for BotFather. (A built-in Telegram bot that helps users create custom Telegram bots)
* Type `/newbot` to create a new bot
* Give your bot a name & a username
* Copy your new Telegram bot’s token. It should be in following format:
```
1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG
```
* For detailed step by step guide, visit this article: [How to setup Slackker with Telegram][setup-telegram]

### Using slackker callbacks with keras callbacks method
Import `slackker.callbacks` with following line:
```python
from slackker.callbacks.keras import slackUpdate, telegramUpdate
```
### Create slackker object for Slack
create slackker object with `slackUpdate`
```python
slack_update = slackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed",
    channel="A04AAB77ABC",
    modelName='Simple_NN',
    export='png',
    sendPlot=True,
    verbose=0)
```
`slackUpdate` takes following arguments:
* `token`: *(string)* Slack app token
* `channel`: *(string)* Slack channel where you want to receive updates *(make sure you have added slack app to this same channel)*
* `modelName`: *(string)* Name for your model. This same name will be used in future for title of the generated plots.
* `export`: *(string)* default `"png"`: Format for plots to be exported. *(supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)*
* `sendPlots`: *(Bool)* default `True`: If set to `True` it will export history of model, both training and validation, save it in the format given in `export` argument and send graphs to slack channel when training ends. If set to `False` it will not send exported graphs to slack channel. 
* `verbose`: *(int)* default `0`: You can sent the verbose level up to 3.
  * `verbose = 0` No logging
  * `verbose = 1` Info logging
  * `verbose = 2` Debug/In-depth logging

### Create slackker object for Telegram
create slackker object with `telegramUpdate`
```python
telegram_update = telegramUpdate(token="1234567890:AAAAA_A111BBBBBCCC2DD3eEe44f5GGGgGG",
    modelName='Simple_NN',
    export='png',
    sendPlot=True,
    verbose=0)
```
`telegramUpdate` takes following arguments:
* `token`: *(string)* Telegram bot token
* `modelName`: *(string)* Name for your model. This same name will be used in future for title of the generated plots.
* `export`: *(string)* default `"png"`: Format for plots to be exported. *(supported formats: eps, jpeg, jpg, pdf, pgf, png, ps, raw, rgba, svg, svgz, tif, tiff)*
* `sendPlots`: *(Bool)* default `True`: If set to `True` it will export history of model, both training and validation, save it in the format given in `export` argument and send graphs to slack channel when training ends. If set to `False` it will not send exported graphs to slack channel. 
* `verbose`: *(int)* default `0`: You can sent the verbose level up to 3.
  * `verbose = 0` No logging
  * `verbose = 1` Info logging
  * `verbose = 2` Debug/In-depth logging

### Call slackker object into callbacks during model fit

Now you can call slackker object into callbacks argument just like any other callbacks object.
```python
history = model.fit(x_train, 
                    y_train,
                    epochs = 3,
                    batch_size = 16,
                    verbose=1,
                    validation_data=(x_val,y_val),
                    callbacks=[slack_update])
```

### Final code
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
slack_update = slackUpdate(token="xoxb-123234234235-123234234235-adedce74748c3844747aed48499bb",
    channel="A04AAB77ABC",
    modelName='SampleModel',
    export='png',
    sendPlot=True,
    verbose=0)

# Call Slackker object in model.fit() callbacks
history = model.fit(x_train, 
                    y_train,
                    epochs = 3,
                    batch_size = 16,
                    verbose=1,
                    validation_data=(x_val,y_val),
                    callbacks=[slack_update])
```

##  Support :sparkles:
If you get stuck, we’re here to help. The following are the best ways to get assistance working through your issue:

* Use our [Github Issue Tracker][gh-issues] for reporting bugs or requesting features.
Contribution are the best way to keep `slackker` amazing :muscle:
* If you want to contribute please refer [Contributor's Guide][gh-contrib] for how to contribute in a helpful and collaborative way :innocent:

#

## Citation :page_facing_up:
Please cite slackker in your publications if this is useful for your project/research. Here is an example BibTeX entry:
```BibTeX
@misc{siddheshgunjal2023slackker,
  title={slackker},
  author={Siddhesh Gunjal},
  year={2023},
  howpublished={\url{https://github.com/siddheshgunjal/slackker}},
}
```

## Maintainer :sunglasses:
* Siddhesh Gunjal
  * [Website][portfolio]
  * [GitHub](https://github.com/siddheshgunjal)
  * [LinkedIn](https://linkedin.com/in/siddheshgunjal)


<!-- Markdown link -->
[slack-sdk]: https://github.com/slackapi/python-slack-sdk
[setup-slack]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-to-monitor-keras-model-training-status-on-slack-9f67265dfabd
[setup-telegram]: https://medium.com/@siddheshgunjal82/how-to-setup-slackker-with-telegram-to-monitor-keras-model-training-21b1ff0c1020
[matplot-lib]: https://github.com/matplotlib/matplotlib
[keras]: https://github.com/keras-team/keras
[py-pi]: https://pypi.org/
[slack-app]: https://api.slack.com/apps
[gh-issues]: https://github.com/siddheshgunjal/slackker/issues
[gh-contrib]: https://github.com/siddheshgunjal/slackker/blob/main/CONTRIBUTING.md
[portfolio]: https://siddheshgunjal.github.io/

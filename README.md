# slackker

``slackker`` is Python package for reporting your ML training status in realtime on slack channel.

# 
**Star this repo if you like it! ⭐️**
#


### Installation
* Install slackker from PyPI (recommended). slackker is compatible with Python 3.6+ and runs on Linux, MacOS X and Windows. 
* Usage as given below:

```bash
pip install slackker
```

#### Import slackker package for keras
```python
from slackker import SLKerasUpdate
```

#### Example:
```python
# Import library for keras
from slackker import SLKerasUpdate

# Train-Test split for your keras model
x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size=0.8)

# Build keras model
model = Sequential()
model.add(Dense(8,activation='relu',input_shape = (IMG_WIDTH, IMG_HEIGHT, DEPTH)))
model.add(Dense(3,activation='softmax'))
model.compile(optimizer = 'rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

# Create Slackker object
slack_update = SLKerasUpdate(token="xoxb-123234234235-123234234235-123234234235-adedce74748c3844747aed48499bb",
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
                    callbacks=[slack_update])
```


#### Citation
Please cite slackker in your publications if this is useful for your research. Here is an example BibTeX entry:
```BibTeX
@misc{siddheshgunjalslackker,
  title={slackker},
  author={Siddhesh Gunjal},
  year={2023},
  howpublished={\url{https://github.com/siddheshgunjal/slackker}},
}
```

### Maintainer
* Siddhesh Gunjal, github: [siddheshgunjal](https://github.com/siddheshgunjal)
* Contributions are welcome.

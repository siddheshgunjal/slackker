# slackker

``Slacki`` is Python package for reporting your ML training status in realtime on slack channel.

# 
**Star this repo if you like it! ⭐️**
#


### Installation
* Install slackker from PyPI (recommended). slackker is compatible with Python 3.6+ and runs on Linux, MacOS X and Windows. 
* A new environment can be created as following:

```bash
pip install slackker
```

#### Import slackker package for keras
```python
ffrom slackker import SLKerasUpdate
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
model.add(Dense(8,activation='relu',input_shape = (4,)))
model.add(Dense(3,activation='softmax'))
model.compile(optimizer = 'rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

sc = slacki(channel='new_channel', token='xoxp-123234234235-123234234235-123234234235-adedce74748c3844747aed48499bb')

# Create Slackker object
slack_update = SLKerasUpdate(token="xoxb-123234234235-123234234235-123234234235-adedce74748c3844747aed48499bb",
    channel="A04AAB77ABC",
    modelName='SampleModel',
    export='png')
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

#### References
* https://github.com/siddheshgunjal/slackker

### Maintainer
* Siddhesh Gunjal, github: [siddheshgunjal](https://github.com/siddheshgunjal)
* Contributions are welcome.
* If you wish to buy me a <a href="https://www.buymeacoffee.com/erdogant">Coffee</a> for this work, it is very appreciated :)

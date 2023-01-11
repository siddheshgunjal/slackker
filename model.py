import numpy as np
import matplotlib.pyplot as plt
import itertools
import tensorflow
from sklearn import datasets
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, KFold, GridSearchCV
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from keras.models import Sequential
from keras.layers import Dense
from keras.utils import to_categorical
from keras.wrappers.scikit_learn import KerasClassifier

from keras.callbacks import ModelCheckpoint, ReduceLROnPlateau

from slackker import SLKerasUpdate

# %matplotlib inline
# # %config InlineBackend.figure_format = 'retina'

seed = 1000

# to supress unneccesary tf warnings
tensorflow.compat.v1.logging.set_verbosity(tensorflow.compat.v1.logging.ERROR)


iris = datasets.load_iris()
x = iris.data
y = to_categorical(iris.target)
labels_names = iris.target_names
xid, yid = 0, 1

le = LabelEncoder()
encoded_labels = le.fit_transform(iris.target_names)

x_train, x_test, y_train, y_test = train_test_split(x, y, train_size=0.8, random_state=seed)
x_train, x_val, y_train, y_val = train_test_split(x_train, y_train, train_size=0.8, random_state=seed)

model = Sequential()
model.add(Dense(8,activation='relu',input_shape = (4,)))
model.add(Dense(3,activation='softmax'))
model.compile(optimizer = 'rmsprop', loss='categorical_crossentropy', metrics=['accuracy'])

# ModelCheckpoint callback
checkpoints = ModelCheckpoint('checkpoints/epoch_{epoch:02d}_loss{val_loss:.3f}.h5',
    monitor='val_acc',
    save_best_only=True,
    save_weights_only=True)

# Slackker Checkpoint
slack_update = SLKerasUpdate(token="xoxb-4615231545733-4603743143687-P0ngiBAuMsp512V5DafGBajT",
    channel="C04JAK77KHQ",
    modelName='SampleModel',
    export='png')

history = model.fit(x_train, 
                    y_train,
                    epochs = 3,
                    batch_size = 16,
                    verbose=1,
                    validation_data=(x_val,y_val),
                    callbacks=[checkpoints, slack_update])

# print(history.history.keys())
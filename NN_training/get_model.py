# Silnence output of tensorflow/keras about GPU status
import os

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Keras/TF imports
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Dense, Flatten, Dropout, Conv2D, MaxPooling2D
from keras.optimizers import Adam
from keras import metrics
from keras.initializers import Orthogonal
from keras.constraints import max_norm
from keras.regularizers import l2


gpus = tf.config.experimental.list_physical_devices("GPU")
for gpu in gpus:
    tf.config.experimental.set_memory_growth(gpu, True)


kernel_initializer = Orthogonal(gain=1.0, seed=None)
kernel_constraint = max_norm(3)
bias_constraint = max_norm(3)


def get_LL(model, tp):
    model.add(
        Conv2D(32, (3, 3), padding="same", activation="relu", input_shape=(32, 32, 1),)
    )
    model.add(
        Conv2D(
            int(tp["filter_units_1"]),
            kernel_size=int(tp["kernel_size_1"]),
            padding="same",
            activation="relu",
        )
    )
    model.add(MaxPooling2D(pool_size=int(tp["max_pool_1"]), padding="same"))
    model.add(
        Conv2D(
            int(tp["filter_units_2"]),
            kernel_size=int(tp["kernel_size_2"]),
            padding="same",
            activation="relu",
        )
    )
    model.add(
        Conv2D(
            int(tp["filter_units_3"]),
            kernel_size=int(tp["kernel_size_3"]),
            padding="same",
            activation="relu",
        )
    )
    model.add(Flatten())
    model.add(Dense(int(tp["dense_units_1"]), activation="relu"))
    model.add(Dropout(tp["dropout_1"]))
    model.add(Dense(int(tp["dense_units_2"]), activation="relu"))
    model.add(Dropout(tp["dropout_2"]))
    return model


def get_HL(model, tp, input_shape):
    model.add(Flatten(input_shape=(input_shape,)))
    for dense_ix in range(int(tp["dense_layers"])):
        model.add(
            Dense(
                tp["dense_units"],
                activation="relu",
                kernel_initializer=kernel_initializer,
                kernel_constraint=kernel_constraint,
                bias_constraint=kernel_constraint,
            )
        )
        if dense_ix - 1 < int(tp["dense_layers"]):
            model.add(Dropout(tp["dropout"]))
    return model


def get_model(run_type, tp, input_shape=None):
    model = Sequential()
    if run_type == "LL":
        model = get_LL(model, tp)

    elif run_type == "HL":
        model = get_HL(model, tp, input_shape)

    model.add(Dense(1, activation="sigmoid"))

    model.compile(
        loss="binary_crossentropy",
        optimizer=Adam(lr=tp["learning_rate"]),
        metrics=["accuracy", metrics.AUC(name="auc")],
    )
    
    return model

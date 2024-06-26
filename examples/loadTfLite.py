# File used to test keras conversion to tf-lite for keras mdn. 
# Uses the same code as 1-sineprediction.py

# Normal imports for everybody
from tensorflow import keras
# Using trick from notebooks/context.py
# little path hack to access module which is one directory up.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import keras_mdn_layer as mdn
import numpy as np

# Converting for tensorflow lite.
import tensorflow as tf


# Generating some data:
NSAMPLE = 3000

y_data = np.float32(np.random.uniform(-10.5, 10.5, NSAMPLE))
r_data = np.random.normal(size=NSAMPLE)
x_data = np.sin(0.75 * y_data) * 7.0 + y_data * 0.5 + r_data * 1.0
x_data = x_data.reshape((NSAMPLE, 1))

N_HIDDEN = 15
N_MIXES = 10

model = keras.Sequential()
model.add(keras.layers.Dense(N_HIDDEN, batch_input_shape=(None, 1), activation='relu'))
model.add(keras.layers.Dense(N_HIDDEN, activation='relu'))
model.add(mdn.MDN(1, N_MIXES))
model.compile(loss=mdn.get_mixture_loss_func(1, N_MIXES), optimizer=keras.optimizers.Adam())
model.summary()

history = model.fit(x=x_data, y=y_data, batch_size=128, epochs=200, validation_split=0.15)







# Sample on some test data:
x_test = np.float32(np.arange(-15, 15, 0.01))
NTEST = x_test.size
print("Testing:", NTEST, "samples.")
x_test = x_test.reshape(NTEST, 1)  # needs to be a matrix, not a vector

# Make predictions from the model
y_test = model.predict(x_test)
# y_test contains parameters for distributions, not actual points on the graph.
# To find points on the graph, we need to sample from each distribution.

# Sample from the predicted distributions
y_samples = np.apply_along_axis(mdn.sample_from_output, 1, y_test, 1, N_MIXES, temp=1.0)

# Split up the mixture parameters (for future fun)
mus = np.apply_along_axis((lambda a: a[:N_MIXES]), 1, y_test)
sigs = np.apply_along_axis((lambda a: a[N_MIXES:2*N_MIXES]), 1, y_test)
pis = np.apply_along_axis((lambda a: mdn.softmax(a[2*N_MIXES:])), 1, y_test)

converter = tf.lite.TFLiteConverter.from_keras_model(model)

# converter.optimizations = [tf.lite.Optimize.DEFAULT]
"""converter.target_spec.supported_ops = [
tf.lite.OpsSet.TFLITE_BUILTINS, # enable TensorFlow Lite ops.
tf.lite.OpsSet.SELECT_TF_OPS, # enable TensorFlow ops.   
]"""
# converter._experimental_lower_tensor_list_ops = False

tflite_model = converter.convert()
tflite_model_name = 'examples/1-sineprediction-lite.tflite'


with open(tflite_model_name, 'wb') as f:
    f.write(tflite_model)

print("Conversion done, bye.")








print("Done.")
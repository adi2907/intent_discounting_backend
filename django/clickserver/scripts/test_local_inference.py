import tensorflow as tf
import numpy as np

model = tf.saved_model.load('/home/ubuntu/clickstream/django/clickserver/clickserver/models/desisandook_savedmodel/1')
serving_func = model.signatures['serving_default']

#input_data = np.array([[[12.0, 39.0], [12.0, 1.0], [12.0, 0.0], [12.0, 0.0], [12.0, 0.0],[12.0, 1.0], [12.0, 0.0], [12.0, 0.0], [12.0, 1.0], [12.0, 0.0]]])
# for input sequence of 5
input_data = np.array([[[12.0, 39.0], [12.0, 1.0], [12.0, 0.0], [12.0, 0.0], [12.0, 0.0]]])

result = serving_func(tf.constant(input_data, dtype=tf.float32))
print("Inference result:", result)

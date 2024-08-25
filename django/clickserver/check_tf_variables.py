import tensorflow as tf

model = tf.saved_model.load('/home/ubuntu/clickstream/django/clickserver/clickserver/models/desisandook_savedmodel/1')

print("Model structure:")
print(model.signatures['serving_default'].structured_outputs)

print("\nModel inputs:")
print(model.signatures['serving_default'].inputs)

print("\nModel outputs:")
print(model.signatures['serving_default'].outputs)

print("\nModel variables:")
for variable in model.signatures['serving_default'].variables:
    print(f"Name: {variable.name}, Shape: {variable.shape}")

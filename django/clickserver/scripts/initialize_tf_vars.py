import tensorflow as tf

# Load the saved model
model = tf.saved_model.load('/home/ubuntu/clickstream/django/clickserver/clickserver/models/desisandook_savedmodel/1')

# If you're using TF 2.x, the variables should already be initialized if they exist. 
# Simply re-save the model to ensure everything is set correctly.

# Re-save the model
tf.saved_model.save(model, '/home/ubuntu/clickstream/django/clickserver/clickserver/models/desisandook_savedmodel/1')


from rest_framework import serializers
from .models import *

# create serializer for user model
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'

# create serializer for item model
class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class PurchaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = '__all__'

class VisitsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visits
        fields = '__all__'
    
class CartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cart
        fields = '__all__'

class IdentifiedUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentifiedUser
        fields = '__all__'

class MostVisitedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['product_id','num_visits']

class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSummary,
        fields = ['user_token', 'last_visited', 'last_carted','recommended']

from rest_framework import serializers
from .models import Order, OrderItem


class OrderItemDetailSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    model_name = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = [
            'title_snapshot',
            'price_snapshot',
            'quantity',
            'listing_id',
            'image',
            'model_name'
        ]

    def get_image(self, obj):
        # ✅ SAFE VERSION
        if obj.listing and obj.listing.images.exists():
            return obj.listing.images.first().image.url
        return None

    def get_model_name(self, obj):
        # ✅ SAFE VERSION
        if obj.listing and obj.listing.vehicle_model:
            return obj.listing.vehicle_model.name
        return None


class OrderDetailSerializer(serializers.ModelSerializer):
    buyer_name = serializers.CharField(source='buyer.username')
    seller_name = serializers.CharField(source='seller.username')
    items = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'id',
            'total_amount',
            'status',
            'created_at',
            'buyer_name',
            'seller_name',
            'items'
        ]

    def get_items(self, obj):
        # ✅ CORRECT (matches related_name='items')
        items = obj.items.all()
        return OrderItemDetailSerializer(items, many=True).data


# 🔹 CREATE ORDER
class CreateOrderSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)


# 🔹 UPDATE STATUS
class UpdateOrderStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['paid', 'cancelled', 'completed'])


# 🔹 BASIC ORDER (for simple endpoints)
class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['title_snapshot', 'price_snapshot', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'buyer',
            'seller',
            'total_amount',
            'status',
            'created_at',
            'items'
        ]
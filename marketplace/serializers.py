from rest_framework import serializers
from .models import VehicleBrand, VehicleModel, Part, Listing, ListingImage

from marketplace.models import Listing

from .models import Wishlist
from rest_framework import serializers
from .models import Wishlist, Listing


class ListingDetailSerializer(serializers.ModelSerializer):
    images = serializers.SerializerMethodField()
    model_name = serializers.CharField(source='vehicle_model.name')
    brand_name = serializers.CharField(source='vehicle_model.brand.name')
    part_name = serializers.CharField(source='part.name')
    seller_name = serializers.CharField(source='seller.username')

    class Meta:
        model = Listing
        fields = [
            'id',
            'title',
            'price',
            'condition',
            'quantity',
            'status',
            'images',
            'model_name',
            'brand_name',
            'part_name',
            'seller_name'
        ]

    def get_images(self, obj):
        return [img.image.url for img in obj.images.all()]


class WishlistSerializer(serializers.ModelSerializer):
    listing = ListingDetailSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'listing', 'created_at']
        
class VehicleBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleBrand
        fields = '__all__'


class VehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleModel
        fields = '__all__'


class PartSerializer(serializers.ModelSerializer):
    class Meta:
        model = Part
        fields = '__all__'


class ListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Listing
        fields = '__all__'
        read_only_fields = ['seller']

class CreateOrderSerializer(serializers.Serializer):
    listing_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1)

class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image']


class ListingSerializer(serializers.ModelSerializer):
    images = ListingImageSerializer(many=True, read_only=True)

    class Meta:
        model = Listing
        fields = '__all__'
        read_only_fields = ['seller']

class ListingImageUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image']


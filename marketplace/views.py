from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.generics import get_object_or_404, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import DestroyAPIView
from .models import VehicleBrand, VehicleModel, Part, Listing, ListingImage, Wishlist
from .serializers import (
    VehicleBrandSerializer,
    VehicleModelSerializer,
    PartSerializer,
    ListingSerializer,
    ListingImageUploadSerializer,
    WishlistSerializer
)

# =========================
# WISHLIST
# =========================

class MyWishlistView(ListAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.select_related(
            'listing__vehicle_model__brand',
            'listing__part',
            'listing__seller'
        ).prefetch_related(
            'listing__images'
        ).filter(
            user=self.request.user
        ).order_by('-created_at')


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# =========================
# VEHICLE DATA
# =========================

class VehicleBrandViewSet(viewsets.ModelViewSet):
    queryset = VehicleBrand.objects.all()
    serializer_class = VehicleBrandSerializer


class VehicleModelViewSet(viewsets.ModelViewSet):
    queryset = VehicleModel.objects.all()
    serializer_class = VehicleModelSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        brand_id = self.request.query_params.get('brand')
        if brand_id:
            queryset = queryset.filter(brand_id=brand_id)
        return queryset


class PartViewSet(viewsets.ModelViewSet):
    queryset = Part.objects.all()
    serializer_class = PartSerializer

# =========================
# LISTINGS
# =========================

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all()
    serializer_class = ListingSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vehicle_model', 'part', 'condition']
    search_fields = ['title', 'description']
    ordering_fields = ['price', 'created_at']

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    # ✅ Support partial updates (PATCH) — only send fields you want to change
    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ✅ Protect PUT/PATCH — only the seller can edit their own listing
    def update(self, request, *args, **kwargs):
        listing = self.get_object()
        if listing.seller != request.user:
            return Response({"error": "Not allowed"}, status=403)
        return super().update(request, *args, **kwargs)

    # ✅ Protect DELETE — only the seller can delete their own listing
    def destroy(self, request, *args, **kwargs):
        listing = self.get_object()
        if listing.seller != request.user:
            return Response({"error": "Not allowed"}, status=403)
        return super().destroy(request, *args, **kwargs)

    # GET /api/listings/my-listings/
    @action(detail=False, methods=['get'], url_path='my-listings', permission_classes=[IsAuthenticated])
    def my_listings(self, request):
        listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    # POST /api/listings/{id}/upload-image/
    @action(
        detail=True,
        methods=['post'],
        url_path='upload-image',
        permission_classes=[IsAuthenticated],
        parser_classes=[MultiPartParser, FormParser]
    )
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        if listing.seller != request.user:
            return Response({"error": "Not allowed"}, status=403)

        serializer = ListingImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(listing=listing)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

# =========================
# IMAGE UPLOAD (standalone view — kept for backwards compat)
# =========================

class UploadListingImageView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, listing_id):
        listing = get_object_or_404(Listing, id=listing_id)

        if listing.seller != request.user:
            return Response({"error": "Not allowed"}, status=403)

        serializer = ListingImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(listing=listing)
            return Response(serializer.data, status=201)

        return Response(serializer.errors, status=400)

# =========================
# DELETE IMAGE
# =========================

class DeleteListingImageView(DestroyAPIView):
    queryset = ListingImage.objects.all()
    permission_classes = [IsAuthenticated]

    def perform_destroy(self, instance):
        if instance.listing.seller != self.request.user:
            raise PermissionDenied("Not allowed")
        instance.delete()

# =========================
# EXTRA
# =========================

class ModelsByBrandView(APIView):
    def get(self, request, brand_id):
        models = VehicleModel.objects.filter(brand_id=brand_id)
        serializer = VehicleModelSerializer(models, many=True)
        return Response(serializer.data)
from django.urls import path
from rest_framework.routers import DefaultRouter
from .views import DeleteListingImageView
from .views import (
    VehicleBrandViewSet,
    VehicleModelViewSet,
    PartViewSet,
    ListingViewSet,
    UploadListingImageView,
    WishlistViewSet,
    MyWishlistView
)

router = DefaultRouter()
router.register(r'brands', VehicleBrandViewSet)
router.register(r'models', VehicleModelViewSet)
router.register(r'parts', PartViewSet)
router.register(r'listings', ListingViewSet)
router.register(r'wishlist', WishlistViewSet, basename='wishlist')

# ✅ DEFINE urlpatterns FIRST
urlpatterns = [
    # 🔥 THIS is your missing route
    path('wishlist/details/', MyWishlistView.as_view(), name='wishlist-details'),
     path('listing-images/<uuid:pk>/', DeleteListingImageView.as_view()),
    path(
        'listings/<uuid:listing_id>/upload-image/',
        UploadListingImageView.as_view(),
        name='upload-listing-image'
    ),
]

# ✅ THEN append router
urlpatterns += router.urls
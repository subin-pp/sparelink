from django.db import transaction
from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.generics import get_object_or_404, ListAPIView

from .models import Order, OrderItem
from .serializers import (
    CreateOrderSerializer,
    UpdateOrderStatusSerializer,
    OrderSerializer,
    OrderDetailSerializer   # ✅ IMPORTANT
)

from marketplace.models import Listing


# 🔹 CREATE ORDER
class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        listing_id = serializer.validated_data['listing_id']
        quantity = serializer.validated_data['quantity']

        try:
            listing = Listing.objects.select_for_update().get(id=listing_id)
        except Listing.DoesNotExist:
            return Response({"error": "Listing not found"}, status=404)

        # Prevent seller buying own listing
        if listing.seller == request.user:
            return Response({"error": "You cannot buy your own listing"}, status=400)

        # Check stock
        if listing.quantity < quantity:
            return Response({"error": "Not enough stock available"}, status=400)

        total_price = listing.price * quantity

        # Create Order
        order = Order.objects.create(
            buyer=request.user,
            seller=listing.seller,
            total_amount=total_price,
            status='pending'
        )

        # Create OrderItem snapshot
        OrderItem.objects.create(
            order=order,
            listing=listing,
            title_snapshot=listing.title,
            price_snapshot=listing.price,
            quantity=quantity
        )

        # Reduce stock
        listing.quantity -= quantity

        if listing.quantity == 0:
            listing.status = 'sold'

        listing.save()

        return Response({
            "message": "Order created successfully",
            "order_id": str(order.id)
        }, status=status.HTTP_201_CREATED)


# 🔹 UPDATE ORDER STATUS
class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        serializer = UpdateOrderStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']

        if order.status in ['cancelled', 'completed']:
            return Response({"error": "Order already finalized"}, status=400)

        if new_status == 'cancelled':
            if request.user != order.buyer:
                return Response({"error": "Only buyer can cancel"}, status=403)
            if order.status != 'pending':
                return Response({"error": "Cannot cancel after payment"}, status=400)
            order.status = 'cancelled'

        elif new_status == 'completed':
            if request.user != order.seller:
                return Response({"error": "Only seller can complete"}, status=403)
            if order.status != 'paid':
                return Response({"error": "Order must be paid before completion"}, status=400)
            order.status = 'completed'

        elif new_status == 'paid':
            if order.status != 'pending':
                return Response({"error": "Order already processed"}, status=400)
            order.status = 'paid'

        order.save()

        return Response({
            "message": "Order status updated",
            "status": order.status
        })


# 🔹 MY PURCHASES
class MyOrdersView(ListAPIView):
    serializer_class = OrderDetailSerializer   # ✅ FIXED
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.select_related('buyer', 'seller')\
            .prefetch_related(
                'items__listing__images',
                'items__listing__vehicle_model'
            )\
            .filter(
                buyer=self.request.user
            )\
            .order_by('-created_at')

# 🔹 MY SALES
class MySalesView(ListAPIView):
    serializer_class = OrderDetailSerializer   # ✅ IMPORTANT
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.select_related('buyer', 'seller')\
            .prefetch_related(
                'items__listing__images',
                'items__listing__vehicle_model'
            )\
            .filter(
                seller=self.request.user
            )\
            .order_by('-created_at')

# 🔥 MAIN API (WHAT YOU WANTED)
class OrderListWithDetailsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        # ✅ Optimized query (NO N+1 problem)
        orders = Order.objects.select_related('buyer', 'seller')\
            .prefetch_related(
                'items__listing__images',
                'items__listing__vehicle_model'
            )\
            .filter(
                Q(buyer=request.user) | Q(seller=request.user)   # ✅ IMPORTANT FILTER
            )\
            .order_by('-created_at')

        serializer = OrderDetailSerializer(orders, many=True)
        return Response(serializer.data)
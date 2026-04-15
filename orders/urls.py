from django.urls import path
from .views import CreateOrderView, UpdateOrderStatusView, MyOrdersView, MySalesView, OrderListWithDetailsView

urlpatterns = [
    path('create/', CreateOrderView.as_view()),
    path('<uuid:order_id>/status/', UpdateOrderStatusView.as_view()),
    path('my-orders/', MyOrdersView.as_view()),
    path('my-sales/', MySalesView.as_view()),

    # ✅ ADD THIS
    path('details/', OrderListWithDetailsView.as_view()),
]

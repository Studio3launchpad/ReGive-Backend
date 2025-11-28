from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import (
   
    CustomLoginView,
    RegisterUserView,
    UserProfileView,
    AdminDashboardView,
    SellerDashboardView,
    BuyerDashboardView,
    MarketplaceDashboardView,
    AddressViewSet,
    CategoryViewSet,
    ItemViewSet,
    PublicItemViewSet,
    ItemReviewViewSet,
    OrderViewSet,
    CartViewSet,
    WishlistViewSet,
    PaymentViewSet,
    NotificationViewSet,
    ItemStatsView,
)

router = DefaultRouter()
router.register("addresses", AddressViewSet, basename="address")
router.register("categories", CategoryViewSet, basename="category")
router.register("items", ItemViewSet, basename="item")
router.register("public-items", PublicItemViewSet, basename="public-item")
router.register("reviews", ItemReviewViewSet, basename="review")
router.register("orders", OrderViewSet, basename="order")
router.register("carts", CartViewSet, basename="cart")
router.register("wishlist", WishlistViewSet, basename="wishlist")
router.register("payments", PaymentViewSet, basename="payment")
router.register("notifications", NotificationViewSet, basename="notification")


urlpatterns = [
    
    path("login/", CustomLoginView.as_view(), name="user-login"),
    path("register/", RegisterUserView.as_view(), name="user-register"),
    path("profile/", UserProfileView.as_view(), name="user-profile"),
    path("dashboard/admin/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("dashboard/seller/", SellerDashboardView.as_view(), name="seller-dashboard"),
    path("dashboard/buyer/", BuyerDashboardView.as_view(), name="buyer-dashboard"),
    path("dashboard/marketplace/", MarketplaceDashboardView.as_view(), name="marketplace-dashboard"),

    
    path("items/<int:pk>/stats/", ItemStatsView.as_view(), name="item-stats"),
    path("", include(router.urls)),
]

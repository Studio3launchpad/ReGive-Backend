from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination

from django_filters.rest_framework import DjangoFilterBackend

from users.models import CustomUser, Address
from items.models import Item, ItemReview, Category
from orders.models import Order, OrderItem
from payments.models import Payment
from notifications.models import Notification
from wishlist.models import Wishlist
from cart.models import Cart, CartItem

from drf_spectacular.utils import extend_schema, extend_schema_view

from api.serializers import (
    CustomLoginSerializer,
    CustomRegisterSerializer,
    UserSerializer,
    AddressSerializer,
    CategorySerializer,
    ItemSerializer,
    ItemReviewSerializer,
    OrderSerializer,
    PaymentSerializer,
    NotificationSerializer,
    WishlistSerializer,
    CartSerializer,
    CartItemSerializer,
    AdminDashboardSerializer,
    SellerDashboardSerializer,
    BuyerDashboardSerializer,
    MarketplaceDashboardSerializer,
)

from api.filters import ItemFilter
from api.permissions import IsBuyer, IsSeller, IsOwnerOrReadOnly, IsApprovedAdmin
from dj_rest_auth.views import LoginView


class DefaultPagination(PageNumberPagination):
    page_size_query_param = "page_size"
    max_page_size = 200



class WishlistAddInputSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()


class CheckoutInputSerializer(serializers.Serializer):
    shipping_address = serializers.IntegerField()


class ItemStatsSerializer(serializers.Serializer):
    item = serializers.CharField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()


# -------------------------
# Auth views
# -------------------------
@extend_schema(tags=["Auth"], summary="Custom login (dj-rest-auth override)")
class CustomLoginView(LoginView):
    serializer_class = CustomLoginSerializer


@extend_schema(tags=["Auth"], request=CustomRegisterSerializer, responses=UserSerializer)
class RegisterUserView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CustomRegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(request)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


@extend_schema(tags=["Auth"], responses=UserSerializer)
class UserProfileView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get(self, request, *args, **kwargs):
        return Response(self.get_serializer(request.user).data)


# -------------------------
# Dashboards (documented)
# -------------------------
@extend_schema_view(get=extend_schema(responses=AdminDashboardSerializer))
@extend_schema(tags=["Dashboard"])
class AdminDashboardView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsApprovedAdmin]
    serializer_class = AdminDashboardSerializer

    def get(self, request, *args, **kwargs):
        data = {
            "total_users": CustomUser.objects.count(),
            "total_items": Item.objects.count(),
            "total_orders": Order.objects.count(),
            "total_reviews": ItemReview.objects.count(),
        }
        # pass data as instance for representation
        serializer = self.get_serializer(data)
        return Response(serializer.data)


@extend_schema_view(get=extend_schema(responses=SellerDashboardSerializer))
@extend_schema(tags=["Dashboard"])
class SellerDashboardView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsSeller]
    serializer_class = SellerDashboardSerializer

    def get(self, request, *args, **kwargs):
        items = Item.objects.filter(seller=request.user)
        data = {
            "items_count": items.count(),
            "category_stats": list(items.values("category__name").annotate(total=Count("id"))),
            "average_rating": round(
                ItemReview.objects.filter(item__seller=request.user).aggregate(avg=Avg("rating"))["avg"] or 0, 2
            ),
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


@extend_schema_view(get=extend_schema(responses=BuyerDashboardSerializer))
@extend_schema(tags=["Dashboard"])
class BuyerDashboardView(GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    serializer_class = BuyerDashboardSerializer

    def get(self, request, *args, **kwargs):
        reviews = ItemReview.objects.filter(reviewer=request.user)
        data = {
            "total_reviews": reviews.count(),
            "average_rating": round(reviews.aggregate(avg=Avg("rating"))["avg"] or 0, 2),
        }
        serializer = self.get_serializer(data)
        return Response(serializer.data)


@extend_schema_view(get=extend_schema(responses=MarketplaceDashboardSerializer))
@extend_schema(tags=["Dashboard"])
class MarketplaceDashboardView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = MarketplaceDashboardSerializer

    def get(self, request, *args, **kwargs):
        top_categories = list(
            Category.objects.annotate(total=Count("items")).order_by("-total")[:5].values("name", "total")
        )
        latest_items = Item.objects.filter(status="PUBLISHED").order_by("-created_at")[:10]
        # MarketplaceDashboardSerializer is expected to accept a dict with keys used inside it
        serializer = self.get_serializer(
            {"top_categories": top_categories, "latest_items": latest_items}
        )
        return Response(serializer.data)


# -------------------------
# Address
# -------------------------
@extend_schema(tags=["Address"])
class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# -------------------------
# Category
# -------------------------
@extend_schema(tags=["Categories"])
class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "slug"
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Category.objects.all()

    @action(detail=True, methods=["get"])
    def items(self, request, slug=None):
        category = get_object_or_404(Category, slug=slug)
        items = Item.objects.filter(category=category, status="PUBLISHED")
        return Response(ItemSerializer(items, many=True).data)


# -------------------------
# Public items
# -------------------------
@extend_schema(tags=["Marketplace"])
class PublicItemViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ItemSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Item.objects.filter(status="PUBLISHED")
    filter_backends = [DjangoFilterBackend]
    filterset_class = ItemFilter
    pagination_class = DefaultPagination


# -------------------------
# Item reviews
# -------------------------
@extend_schema(tags=["Reviews"])
class ItemReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ItemReviewSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return ItemReview.objects.filter(reviewer=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reviewer=self.request.user)


# -------------------------
# Wishlist
# -------------------------
@extend_schema(tags=["Wishlist"])
class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)

    @action(detail=False, methods=["post"])
    @extend_schema(
        request=WishlistAddInputSerializer,
        responses=WishlistSerializer,
        description="Add item to wishlist. Provide {\"item_id\": <id>}"
    )
    def add(self, request):
        input_ser = WishlistAddInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        item_id = input_ser.validated_data["item_id"]
        item = get_object_or_404(Item, id=item_id)
        obj, created = Wishlist.objects.get_or_create(user=request.user, item=item)
        if not created:
            return Response({"message": "Item already in wishlist"})
        return Response(WishlistSerializer(obj).data, status=201)

    @action(detail=False, methods=["post"])
    def remove(self, request):
        item_id = request.data.get("item_id")
        Wishlist.objects.filter(user=request.user, item_id=item_id).delete()
        return Response({"message": "Item removed"})


# -------------------------
# Cart (with checkout)
# -------------------------
@extend_schema(tags=["Cart"])
class CartViewSet(viewsets.ModelViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Cart.objects.filter(buyer=self.request.user)

    @action(detail=False, methods=["post"], url_path="checkout")
    @extend_schema(
        request=CheckoutInputSerializer,
        responses=OrderSerializer,
        description="Checkout the current cart. Provide {\"shipping_address\": <id>}"
    )
    def checkout(self, request):
        input_ser = CheckoutInputSerializer(data=request.data)
        input_ser.is_valid(raise_exception=True)
        shipping_address_id = input_ser.validated_data["shipping_address"]

        user = request.user
        try:
            cart = Cart.objects.get(buyer=user)
        except Cart.DoesNotExist:
            return Response({"error": "Cart is empty"}, status=400)

        cart_items = cart.items.all()
        if not cart_items.exists():
            return Response({"error": "Cart is empty"}, status=400)

        shipping_address = get_object_or_404(Address, id=shipping_address_id, user=user)

        order = Order.objects.create(buyer=user, shipping_address=shipping_address, total_amount=0)
        total = 0

        for ci in cart_items:
            item = ci.item
            qty = ci.quantity

            if item.stock < qty:
                return Response({"error": f"Not enough stock for {item.name}"}, status=400)

            item.stock -= qty
            item.save()

            price = 0 if item.is_free else item.price * qty
            total += price

            OrderItem.objects.create(order=order, item=item, quantity=qty, price=price)

        order.total_amount = total
        order.save()

        cart.items.all().delete()

        return Response({"message": "Checkout successful", "order": OrderSerializer(order).data}, status=status.HTTP_201_CREATED)

    def perform_create(self, serializer):
        serializer.save(buyer=self.request.user)

    @action(detail=True, methods=["post"])
    def add_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get("item")
        quantity = int(request.data.get("quantity", 1))
        item = get_object_or_404(Item, id=item_id)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, item=item, defaults={"quantity": quantity})
        if not created:
            cart_item.quantity += quantity
            cart_item.save()
        return Response(CartItemSerializer(cart_item).data)

    @action(detail=True, methods=["post"])
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get("item")
        CartItem.objects.filter(cart=cart, item_id=item_id).delete()
        return Response({"message": "Item removed"})

    @action(detail=True, methods=["post"])
    def clear(self, request, pk=None):
        cart = self.get_object()
        cart.items.all().delete()
        return Response({"message": "Cart cleared"})


# -------------------------
# Orders & Payments
# -------------------------
@extend_schema(tags=["Orders"])
class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsBuyer]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)

    def perform_create(self, serializer):
        serializer.save()

    # seller "my orders" (orders that contain seller's items)
    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated, IsSeller])
    @extend_schema(responses=OrderSerializer(many=True))
    def my_orders_for_seller(self, request):
        # all orders where at least one order item belongs to request.user
        orders = Order.objects.filter(items__item__seller=request.user).distinct()
        return Response(OrderSerializer(orders, many=True).data)


@extend_schema(tags=["Payments"])
class PaymentViewSet(viewsets.ModelViewSet):
    serializer_class = PaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user)

    @extend_schema(request=PaymentSerializer, responses=PaymentSerializer)
    def perform_create(self, serializer):
        # Save with user for audit
        payment = serializer.save(user=self.request.user)

        order = payment.order
        order.status = "PAID"
        order.save()

        # send notification for sellers
        for oi in order.items.all():
            Notification.objects.create(
                user=oi.item.seller,
                title="New Order",
                message=f"{order.buyer.full_name} ordered {oi.item.name} (qty {oi.quantity})."
            )

        # notify buyer
        Notification.objects.create(user=order.buyer, title="Payment Received", message=f"Payment for order #{order.id} received.")

        return payment


# -------------------------
# Notifications
# -------------------------
@extend_schema(tags=["Notifications"])
class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = DefaultPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by("-created_at")

    @action(detail=True, methods=["post"])
    @extend_schema(request=None, responses=NotificationSerializer)
    def read(self, request, pk=None):
        n = get_object_or_404(Notification, pk=pk, user=request.user)
        n.is_read = True
        n.save(update_fields=["is_read"])
        return Response(NotificationSerializer(n).data)


# -------------------------
# Item stats
# -------------------------
@extend_schema(tags=["Items"], responses=ItemStatsSerializer)
class ItemStatsView(GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ItemStatsSerializer

    def get(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        reviews = item.reviews.all()
        data = {
            "item": item.name,
            "average_rating": round(reviews.aggregate(avg=Avg("rating"))["avg"] or 0, 2),
            "total_reviews": reviews.count(),
        }
        return Response(self.get_serializer(data).data)


# -------------------------
# CRUD for Items (sellers create/update/delete)
# -------------------------
@extend_schema(tags=["Items"])
class ItemViewSet(viewsets.ModelViewSet):
    serializer_class = ItemSerializer
    queryset = Item.objects.all()
    filter_backends = [DjangoFilterBackend]
    filterset_class = ItemFilter
    pagination_class = DefaultPagination

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        elif self.action in ("create",):
            return [permissions.IsAuthenticated(), IsSeller()]
        else:
            return [permissions.IsAuthenticated(), IsOwnerOrReadOnly()]

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and (user.is_superuser or getattr(user, "role", None) == "SELLER"):
            if user.is_superuser:
                return Item.objects.all()
            return Item.objects.filter(seller=user)
        return Item.objects.filter(status="PUBLISHED")

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

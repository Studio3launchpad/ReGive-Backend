from rest_framework import serializers
from django.contrib.auth import authenticate
from django.db.models import Q, Avg
import re
from drf_spectacular.utils import extend_schema_field, OpenApiTypes
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import LoginSerializer
from users.models import CustomUser, Profile, Address
from items.models import Category, Item, ItemReview
from orders.models import Order, OrderItem
from payments.models import Payment
from notifications.models import Notification
from wishlist.models import Wishlist
from cart.models import Cart, CartItem


from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from users.models import CustomUser



class CustomRegisterSerializer(serializers.Serializer):
    username = None

    full_name = serializers.CharField(required=True)

    #ROLE CHOICES — remove ADMIN completely
    role = serializers.ChoiceField(
        choices=[
            (CustomUser.Roles.BUYER, "Buyer"),
            (CustomUser.Roles.SELLER, "Seller"),
        ],
        required=True
    )

    email = serializers.EmailField(required=True)

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        return attrs

    def save(self, request):
        data = self.validated_data
        return CustomUser.objects.create_user(
            email=data["email"],
            full_name=data["full_name"],
            role=data["role"],    # seller or buyer only
            password=data["password"],
        )




class CustomLoginSerializer(LoginSerializer):
    username = None  # remove username field
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email and password are required.")

        user = authenticate(
            request=self.context.get("request"),
            username=email,   # authenticate using email
            password=password
        )

        if not user:
            raise serializers.ValidationError("Invalid login credentials.")

        attrs["user"] = user
        return attrs



class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["phone_number", "bio", "avatar", "birth_date"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "is_verified",
            "date_joined",
            "profile",
        ]




class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ["id", "street", "city", "state", "country"]
        read_only_fields = ["user"]


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "slug", "description"]



class ItemSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)
    reviews_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Item
        fields = [
            "id", "name", "slug", "description", "category",
            "condition", "is_free", "price", "is_negotiable",
            "stock", "location", "status",
            "image", "video",
            "created_at", "updated_at",
            "seller", "reviews_count", "average_rating",
        ]

    @extend_schema_field(OpenApiTypes.INT)
    def get_reviews_count(self, obj):
        return obj.reviews.count()

    @extend_schema_field(OpenApiTypes.FLOAT)
    def get_average_rating(self, obj):
        avg = obj.reviews.aggregate(avg=Avg("rating"))["avg"]
        return round(avg or 0, 2)


class ItemReviewSerializer(serializers.ModelSerializer):
    reviewer = UserSerializer(read_only=True)

    class Meta:
        model = ItemReview
        fields = ["id", "item", "reviewer", "rating", "comment", "created_at"]



class OrderItemCreateSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all())
    quantity = serializers.IntegerField(min_value=1)


class OrderItemSerializer(serializers.ModelSerializer):
    item_name = serializers.ReadOnlyField(source="item.name")

    class Meta:
        model = OrderItem
        fields = ["id", "item", "item_name", "quantity", "price"]


class OrderSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    items = OrderItemCreateSerializer(many=True, help_text='Format: [{"item": 1, "quantity": 2}]')
    shipping_address = serializers.PrimaryKeyRelatedField(queryset=Address.objects.all())

    class Meta:
        model = Order
        fields = [
            "id",
            "buyer",
            "shipping_address",
            "items",
            "total_amount",
            "created_at",
        ]
        read_only_fields = ["id", "buyer", "total_amount", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        buyer = self.context["request"].user

        # create order with initial zero amount -> we'll set total after items added
        order = Order.objects.create(buyer=buyer, **validated_data, total_amount=0)
        total = 0

        for item_data in items_data:
            item = item_data["item"]
            quantity = item_data["quantity"]

            if item.stock < quantity:
                raise serializers.ValidationError(
                    f"Not enough stock for {item.name}. Available: {item.stock}"
                )

            item.stock -= quantity
            item.save()

            price = 0 if item.is_free else item.price * quantity
            total += price

            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=quantity,
                price=price
            )

        order.total_amount = total
        order.save()
        return order



class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        read_only_fields = ["reference", "user"]



class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class WishlistSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "item", "added_at"]


class WishlistAddInputSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()

class CheckoutInputSerializer(serializers.Serializer):
    shipping_address = serializers.IntegerField()



class CartItemSerializer(serializers.ModelSerializer):
    item_detail = ItemSerializer(source='item', read_only=True)

    class Meta:
        model = CartItem
        fields = ["id", "item", "item_detail", "quantity", "subtotal"]


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)

    class Meta:
        model = Cart
        fields = ["id", "buyer", "items", "total_amount", "created_at", "updated_at"]
        read_only_fields = ["buyer", "created_at", "updated_at", "total_amount"]



class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_items = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_reviews = serializers.IntegerField()


class SellerDashboardSerializer(serializers.Serializer):
    items_count = serializers.IntegerField()
    category_stats = serializers.ListField(child=serializers.DictField())
    average_rating = serializers.FloatField()


class BuyerDashboardSerializer(serializers.Serializer):
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()


class MarketplaceDashboardSerializer(serializers.Serializer):
    top_categories = serializers.ListField(child=serializers.DictField())
    latest_items = ItemSerializer(many=True)


class ItemStatsSerializer(serializers.Serializer):
    item = serializers.CharField()
    average_rating = serializers.FloatField()
    total_reviews = serializers.IntegerField()

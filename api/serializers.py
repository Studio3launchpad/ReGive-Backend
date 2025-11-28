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


class CustomRegisterSerializer(RegisterSerializer):
    username = None
    email = serializers.EmailField(required=True)
    full_name = serializers.CharField(required=True)
    phone_number = serializers.CharField(required=True)
    role = serializers.ChoiceField(choices=CustomUser.Roles.choices)
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ["email", "full_name", "phone_number", "role", "password1", "password2"]

    def validate_phone_number(self, value):
        normalized = re.sub(r"\D", "", value)
        if CustomUser.objects.filter(phone_number=normalized).exists():
            raise serializers.ValidationError("Phone number already exists.")
        return normalized

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['full_name'] = self.validated_data.get('full_name', '')
        data['phone_number'] = self.validated_data.get('phone_number', '')
        data['role'] = self.validated_data.get('role', CustomUser.Roles.BUYER)
        return data

    def save(self, request):
        data = self.get_cleaned_data()
        return CustomUser.objects.create_user(
            email=data["email"],
            password=data["password1"],
            full_name=data["full_name"],
            phone_number=data["phone_number"],
            role=data["role"],
        )


class CustomLoginSerializer(LoginSerializer):
    username = None
    phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        identifier = attrs["phone"]
        password = attrs["password"]

        user = CustomUser.objects.filter(
            Q(email__iexact=identifier) | Q(phone_number=identifier)
        ).first()

        if user:
            user = authenticate(
                self.context["request"],
                username=user.email,
                password=password,
            )

        if not user:
            raise serializers.ValidationError("Invalid login credentials.")

        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ["bio", "avatar", "website", "birth_date"]


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            "id", "email", "full_name",
            "phone_number", "role",
            "is_verified", "date_joined",
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
        fields = ["id", "order", "amount", "provider", "status", "reference", "created_at"]
        read_only_fields = ["status", "created_at"]



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

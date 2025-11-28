from rest_framework import permissions

def get_role(user):
    """Returns user.role in uppercase, or empty string."""
    return (getattr(user, "role", "") or "").upper()

class RolePermission(permissions.BasePermission):
    """
    Base class for role-based permissions.
    Subclasses must define allowed_roles = ["ROLE1", "ROLE2"]
    """
    allowed_roles = []

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated 
            and get_role(request.user) in self.allowed_roles
        )


class IsSeller(RolePermission):
    allowed_roles = ["SELLER"]


class IsBuyer(RolePermission):
    allowed_roles = ["BUYER"]


class IsAdmin(RolePermission):
    allowed_roles = ["ADMIN"]


class IsSellerOrAdmin(RolePermission):
    allowed_roles = ["SELLER", "ADMIN"]


class IsBuyerOrAdmin(RolePermission):
    allowed_roles = ["BUYER", "ADMIN"]


class IsBuyerOrSeller(RolePermission):
    allowed_roles = ["BUYER", "SELLER"]



class IsApprovedAdmin(permissions.BasePermission):
    """Superuser-only access"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_superuser



class IsVerifiedUser(permissions.BasePermission):
    """User must have is_verified=True."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and getattr(request.user, "is_verified", False)
        )


class IsVerifiedSellerOrAdmin(permissions.BasePermission):
    """
    Verified seller OR admin.
    (This now works even without IsVerifiedSeller.)
    """
    def has_permission(self, request, view):
        user = request.user
        return (
            user.is_authenticated
            and (
                user.is_superuser
                or (get_role(user) == "SELLER" and getattr(user, "is_seller_verified", False))
            )
        )



class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allows full access to object's owner.
    Allows read-only for others.
    Supports models having fields:
        - user
        - seller
        - buyer
    """
    owner_fields = ["user", "seller", "buyer"]

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return any(
            getattr(obj, field, None) == request.user
            for field in self.owner_fields
        )


class IsSellerOfItem(permissions.BasePermission):
    """Only the seller of the item can modify it."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.seller == request.user


class IsBuyerOfOrder(permissions.BasePermission):
    """Only the buyer who placed the order can access or edit it."""
    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and obj.buyer == request.user



class IsNotDeletedUser(permissions.BasePermission):
    """Blocks soft-deleted users."""
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated 
            and not getattr(request.user, "is_deleted", False)
        )



class SellerReadOnlyIfUnverified(permissions.BasePermission):
    """
    Unverified sellers → read-only.
    Verified sellers → full access.
    Non-sellers → normal behavior.
    """
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if get_role(user) != "SELLER":
            return True

        if getattr(user, "is_seller_verified", False):
            return True  

        return request.method in permissions.SAFE_METHODS


class CanCreateItem(permissions.BasePermission):
    """
    Only verified sellers and admins can create items.
    """
    def has_permission(self, request, view):
        user = request.user

        if not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        return (
            get_role(user) == "SELLER"
            and getattr(user, "is_seller_verified", False)
        )


class CanReviewItem(permissions.BasePermission):
    """
    Only buyers can review items.
    Sellers cannot review their own items.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and get_role(request.user) == "BUYER"

    def has_object_permission(self, request, view, item):
        return item.seller != request.user


class CanOrderItem(permissions.BasePermission):
    """
    Buyers only. Cannot buy your own items.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and get_role(request.user) == "BUYER"

    def has_object_permission(self, request, view, item):
        return item.seller != request.user


class IsItemSeller(permissions.BasePermission):
    """
    Used in views that implement get_item() (e.g., upload media).
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        item = view.get_item()
        return item.seller == request.user

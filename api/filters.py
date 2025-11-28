import django_filters
from items.models import Item
from users.models import CustomUser


class ItemFilter(django_filters.FilterSet):
    """
    Filters for Items:
    - Search by name
    - Category slug
    - Condition, status
    - Seller email or role
    - Price range
    - Date range
    - Location search
    - Free/paid filter
    """

    #Text search
    search = django_filters.CharFilter(
        method="filter_search",
        label="Search (name or description)"
    )

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            name__icontains=value
        ) | queryset.filter(
            description__icontains=value
        )

    #Category slug
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="iexact",
        label="Category slug"
    )

    #Condition & status
    condition = django_filters.ChoiceFilter(
        choices=Item.CONDITION_CHOICES,
        label="Condition"
    )

    status = django_filters.CharFilter(
        field_name="status",
        lookup_expr="iexact",
        label="Status"
    )

    #Seller filters
    seller = django_filters.CharFilter(
        field_name="seller__email",
        lookup_expr="icontains",
        label="Seller email"
    )

    seller_role = django_filters.ChoiceFilter(
        field_name="seller__role",
        choices=CustomUser.Roles.choices,
        label="Seller role"
    )

    #Price range
    price_min = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="gte",
        label="Min price"
    )

    price_max = django_filters.NumberFilter(
        field_name="price",
        lookup_expr="lte",
        label="Max price"
    )

    #Date filtering
    created_after = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte"
    )

    created_before = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte"
    )

    #Location
    location = django_filters.CharFilter(
        field_name="location",
        lookup_expr="icontains",
        label="Location search"
    )

    #Free items only
    is_free = django_filters.BooleanFilter(
        field_name="is_free",
        label="Free items only"
    )

    class Meta:
        model = Item
        fields = [
            "search",
            "category",
            "condition",
            "status",
            "seller",
            "seller_role",
            "price_min",
            "price_max",
            "created_after",
            "created_before",
            "location",
            "is_free",
        ]

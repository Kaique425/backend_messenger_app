import django_filters

from .models import Contact


class ContactFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="exact")
    email = django_filters.CharFilter(lookup_expr="exact")
    phone = django_filters.CharFilter(lookup_expr="exact")
    edited_name = django_filters.CharFilter(lookup_expr="exact")
    start_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Start date",
    )
    end_date = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="End date",
    )

    class Meta:
        model = Contact
        fields = (
            "name",
            "email",
            "phone",
            "edited_name",
            "start_date",
            "end_date",
        )

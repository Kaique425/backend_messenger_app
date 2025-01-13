import django_filters

from .models import Contact


class ContactFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr="exact")
    email = django_filters.CharFilter(lookup_expr="exact")
    phone = django_filters.CharFilter(lookup_expr="exact")
    editedName = django_filters.CharFilter(lookup_expr="exact")
    startDate = django_filters.DateFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Start date",
    )
    endDate = django_filters.DateFilter(
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
            "editedName",
            "startDate",
            "endDate",
        )

class SuperuserEditMixin:
    """Superusers have full access. Staff with group permissions can add/change/delete."""

    def has_add_permission(self, request):
        return request.user.is_superuser or super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser or super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or super().has_delete_permission(request, obj)

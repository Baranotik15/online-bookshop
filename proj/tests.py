from unittest.mock import MagicMock
from proj.admin_mixins import SuperuserEditMixin


class _Base:
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class _Admin(SuperuserEditMixin, _Base):
    pass


def _req(is_superuser):
    req = MagicMock()
    req.user.is_superuser = is_superuser
    return req


def test_superuser_has_add_permission():
    assert _Admin().has_add_permission(_req(True)) is True


def test_superuser_has_change_permission():
    assert _Admin().has_change_permission(_req(True)) is True


def test_superuser_has_delete_permission():
    assert _Admin().has_delete_permission(_req(True)) is True


def test_non_superuser_fallback_to_base_add():
    assert _Admin().has_add_permission(_req(False)) is False


def test_non_superuser_fallback_to_base_change():
    assert _Admin().has_change_permission(_req(False)) is False


def test_non_superuser_fallback_to_base_delete():
    assert _Admin().has_delete_permission(_req(False)) is False

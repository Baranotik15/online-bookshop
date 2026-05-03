from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


GROUPS = {
    'Редактори каталогу': {
        'books': ['book', 'author', 'genre'],
    },
    'Менеджери замовлень': {
        'orders': ['order', 'orderitem'],
    },
    'Адміністратори користувачів': {
        'users': ['user'],
    },
}

ACTIONS = ['add', 'change', 'delete', 'view']


class Command(BaseCommand):
    help = 'Create default admin groups with permissions'

    def handle(self, *args, **kwargs):
        for group_name, apps in GROUPS.items():
            group, created = Group.objects.get_or_create(name=group_name)
            permissions = []

            for app_label, models in apps.items():
                for model_name in models:
                    try:
                        ct = ContentType.objects.get(app_label=app_label, model=model_name)
                    except ContentType.DoesNotExist:
                        self.stdout.write(self.style.WARNING(f'  ContentType not found: {app_label}.{model_name}'))
                        continue
                    for action in ACTIONS:
                        perm = Permission.objects.filter(content_type=ct, codename=f'{action}_{model_name}').first()
                        if perm:
                            permissions.append(perm)

            group.permissions.set(permissions)
            status = 'created' if created else 'updated'
            self.stdout.write(self.style.SUCCESS(f'[{status}] {group_name} — {len(permissions)} permissions'))

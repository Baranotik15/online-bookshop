from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand


GROUPS = {
    'Edit Books': {
        'books': ['book', 'author', 'genre'],
    },
    'Edit Orders': {
        'orders': ['order', 'orderitem'],
    },
    'Edit Users': {
        'users': ['user'],
    },
}

ACTIONS = ['add', 'change', 'delete', 'view']


class Command(BaseCommand):
    help = 'Create default admin groups with permissions'

    def handle(self, *args, **kwargs):
        deleted, _ = Group.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'Deleted {deleted} existing groups'))

        for group_name, apps in GROUPS.items():
            group = Group.objects.create(name=group_name)
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
            self.stdout.write(self.style.SUCCESS(f'[created] {group_name} — {len(permissions)} permissions'))

"""
Creates VaultAccess records for any users that don't have one.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from securemyassets.models import VaultAccess

class Command(BaseCommand):
    help = 'Creates VaultAccess records for any users that don\'t have one'

    def handle(self, *args, **kwargs):
        users_without_access = User.objects.filter(vaultaccess=None)
        count = 0
        
        for user in users_without_access:
            VaultAccess.objects.create(user=user)
            count += 1
        
        if count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created {count} VaultAccess records')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('All users already have VaultAccess records')
            )
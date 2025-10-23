"""
Creates a staff user with the specified username and password.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from securemyassets.models import VaultAccess

class Command(BaseCommand):
    help = 'Creates a staff user for testing'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='reviewer', type=str)
        parser.add_argument('--password', default='reviewpass123', type=str)
        parser.add_argument('--email', default='reviewer@example.com', type=str)

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        password = kwargs['password']
        email = kwargs['email']

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'User {username} already exists'))
            user = User.objects.get(username=username)
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            self.stdout.write(self.style.SUCCESS(f'Created user: {username}'))
            
        # Make user staff and create VaultAccess
        user.is_staff = True
        user.save()
        
        VaultAccess.objects.get_or_create(user=user)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'''
                Successfully set up staff user:
                Username: {username}
                Password: {password}
                Email: {email}
                Staff Status: True
                '''
            )
        )
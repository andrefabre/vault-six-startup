from django.test import TestCase
from django.contrib.auth.models import User
from securemyassets.models import Asset, VaultAccess, ProbateGrant
from django.core.exceptions import ValidationError

class AssetModelTest(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_asset_creation(self):
        """Test that an asset can be created with valid data"""
        asset = Asset.objects.create(
            user=self.user,
            name='Test Asset',
            category='SOCIAL',
            note='Test note'
        )
        self.assertEqual(asset.name, 'Test Asset')
        self.assertEqual(asset.category, 'SOCIAL')
        self.assertEqual(asset.user, self.user)

    def test_asset_str_representation(self):
        """Test the string representation of an Asset"""
        asset = Asset.objects.create(
            user=self.user,
            name='Test Asset',
            category='FINANCIAL'
        )
        self.assertEqual(str(asset), 'Financial - Test Asset')

    def test_invalid_category(self):
        """Test that an invalid category raises ValidationError"""
        with self.assertRaises(ValidationError):
            asset = Asset(
                user=self.user,
                name='Test Asset',
                category='INVALID'
            )
            asset.full_clean()

class VaultAccessModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )

    def test_vault_access_creation(self):
        """Test VaultAccess creation with default values"""
        vault_access = VaultAccess.objects.create(user=self.user)
        self.assertEqual(vault_access.user, self.user)
        self.assertFalse(vault_access.granted)
        self.assertIsNone(vault_access.granted_at)

    def test_vault_access_str_representation(self):
        """Test the string representation of VaultAccess"""
        vault_access = VaultAccess.objects.create(user=self.user)
        expected_str = f'Vault access for {self.user.username}'
        self.assertEqual(str(vault_access), expected_str)

class ProbateGrantModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            email='staff@example.com',
            is_staff=True
        )

    def test_probate_grant_creation(self):
        """Test ProbateGrant creation with default status"""
        probate = ProbateGrant.objects.create(
            user=self.user,
            file='test_doc.pdf'
        )
        self.assertEqual(probate.user, self.user)
        self.assertEqual(probate.status, 'UPLOADED')
        self.assertIsNone(probate.reviewed_at)
        self.assertIsNone(probate.reviewed_by)

    def test_probate_grant_status_choices(self):
        """Test that invalid status raises ValidationError"""
        with self.assertRaises(ValidationError):
            probate = ProbateGrant(
                user=self.user,
                file='test_doc.pdf',
                status='INVALID'
            )
            probate.full_clean()

    def test_probate_grant_str_representation(self):
        """Test the string representation of ProbateGrant"""
        probate = ProbateGrant.objects.create(
            user=self.user,
            file='test_doc.pdf'
        )
        expected_str = f'Probate grant for {self.user.username}'
        self.assertEqual(str(probate), expected_str)
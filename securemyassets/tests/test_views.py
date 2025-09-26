from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from securemyassets.models import Asset, VaultAccess, ProbateGrant
from django.core.files.uploadedfile import SimpleUploadedFile

class ViewTests(TestCase):
    def setUp(self):
        # Create regular test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com'
        )
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            email='staff@example.com',
            is_staff=True
        )
        # Create test client
        self.client = Client()

    def test_home_view_unauthenticated(self):
        """Test home view for unauthenticated user"""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/home.html')

    def test_home_view_authenticated(self):
        """Test home view redirects for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_dashboard_view_unauthenticated(self):
        """Test dashboard view requires authentication"""
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_view_authenticated(self):
        """Test dashboard view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/dashboard.html')

    def test_assets_view(self):
        """Test assets view functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Test GET request
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/assets.html')

        # Test POST request to create asset
        asset_data = {
            'name': 'Test Asset',
            'category': 'SOCIAL',
            'note': 'Test note'
        }
        response = self.client.post(reverse('assets'), asset_data)
        self.assertRedirects(response, reverse('assets'))
        self.assertTrue(Asset.objects.filter(name='Test Asset').exists())

    def test_requests_view(self):
        """Test requests view functionality"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('requests'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/requests.html')

    def test_review_queue_access(self):
        """Test review queue access restrictions"""
        # Test access denied for regular user
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('review_queue'))
        self.assertEqual(response.status_code, 403)

        # Test access granted for staff user
        self.client.login(username='staffuser', password='staffpass123')
        response = self.client.get(reverse('review_queue'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/review_queue.html')

    def test_probate_upload(self):
        """Test probate upload functionality"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create dummy PDF file
        dummy_pdf = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )

        response = self.client.post(reverse('probate_upload'), {'document': dummy_pdf})
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(ProbateGrant.objects.filter(user=self.user).exists())
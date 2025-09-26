# Part 5: Testing Implementation

## Overview
This part covers comprehensive testing strategies for the Digital Asset Security application, including:
- Unit testing
- Integration testing
- Security testing
- Coverage reporting
- Test automation

## Step-by-Step Implementation

### Step 1: Test Configuration

1. Update settings.py for testing
```python
# securemyassets/settings.py

# Test-specific settings
if 'test' in sys.argv:
    # Use faster password hasher during tests
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    
    # Use in-memory email backend for tests
    EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    
    # Use faster database for testing
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:'
        }
    }
```

2. Create test utilities
```python
# securemyassets/tests/utils.py

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import Asset, ProbateRequest

def create_test_user(username='testuser', password='testpass123', **kwargs):
    """Create a test user with given credentials."""
    return User.objects.create_user(
        username=username,
        password=password,
        **kwargs
    )

def create_test_asset(user, **kwargs):
    """Create a test asset for given user."""
    defaults = {
        'name': 'Test Asset',
        'category': 'FINANCIAL',
        'note': 'Test note'
    }
    defaults.update(kwargs)
    return Asset.objects.create(user=user, **defaults)

def create_test_file(name='test.pdf', content=b'test content'):
    """Create a test file for uploads."""
    return SimpleUploadedFile(
        name,
        content,
        content_type='application/pdf'
    )

def create_test_probate_request(deceased_user, **kwargs):
    """Create a test probate request."""
    defaults = {
        'requestor_name': 'John Doe',
        'requestor_email': 'john@example.com',
        'relationship': 'EXECUTOR',
        'status': 'PENDING'
    }
    defaults.update(kwargs)
    return ProbateRequest.objects.create(
        deceased_user=deceased_user,
        **defaults
    )
```

### Step 2: Model Tests

1. Create comprehensive model tests
```python
# securemyassets/tests/test_models.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from ..models import Asset, ProbateRequest, ProbateAccess
from .utils import create_test_user, create_test_asset

class AssetModelTest(TestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_asset_creation(self):
        """Test basic asset creation."""
        asset = create_test_asset(self.user)
        self.assertEqual(str(asset), 'Test Asset')
        self.assertEqual(asset.user, self.user)

    def test_asset_categories(self):
        """Test all asset categories are valid."""
        for category, _ in Asset.CATEGORY_CHOICES:
            asset = create_test_asset(
                self.user,
                category=category
            )
            self.assertEqual(asset.category, category)

    def test_asset_validation(self):
        """Test asset validation rules."""
        # Test invalid category
        with self.assertRaises(ValidationError):
            asset = Asset(
                user=self.user,
                name='Test',
                category='INVALID'
            )
            asset.full_clean()

class ProbateRequestModelTest(TestCase):
    def setUp(self):
        self.user = create_test_user()
        self.staff = create_test_user('staffuser', is_staff=True)

    def test_probate_request_creation(self):
        """Test basic probate request creation."""
        request = create_test_probate_request(self.user)
        self.assertEqual(request.status, 'PENDING')
        self.assertEqual(request.deceased_user, self.user)

    def test_probate_request_workflow(self):
        """Test probate request status transitions."""
        request = create_test_probate_request(self.user)
        
        # Test approval
        request.approve(self.staff)
        self.assertEqual(request.status, 'VERIFIED')
        self.assertEqual(request.reviewed_by, self.staff)
        self.assertIsNotNone(request.review_date)
        
        # Test rejection
        request = create_test_probate_request(self.user)
        request.reject(self.staff, 'Invalid documentation')
        self.assertEqual(request.status, 'REJECTED')
        self.assertEqual(request.notes, 'Invalid documentation')

    def test_probate_access_token(self):
        """Test probate access token functionality."""
        request = create_test_probate_request(self.user)
        
        access = ProbateAccess.objects.create(
            probate_request=request,
            access_token='test123',
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        self.assertTrue(access.is_valid())
        
        # Test expiration
        access.expires_at = timezone.now() - timedelta(days=1)
        access.save()
        self.assertFalse(access.is_valid())
```

### Step 3: Form Tests

1. Create form tests
```python
# securemyassets/tests/test_forms.py

from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from ..forms import AssetForm, ProbateRequestForm, ProbateReviewForm
from .utils import create_test_user, create_test_file

class AssetFormTest(TestCase):
    def setUp(self):
        self.user = create_test_user()

    def test_asset_form_valid(self):
        """Test valid asset form submission."""
        form_data = {
            'name': 'Test Asset',
            'category': 'FINANCIAL',
            'note': 'Test note'
        }
        form = AssetForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_asset_form_invalid(self):
        """Test invalid asset form submission."""
        form_data = {
            'name': '',  # Required field
            'category': 'FINANCIAL'
        }
        form = AssetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class ProbateRequestFormTest(TestCase):
    def setUp(self):
        self.test_file = create_test_file()

    def test_probate_request_form_valid(self):
        """Test valid probate request form submission."""
        form_data = {
            'requestor_name': 'John Doe',
            'requestor_email': 'john@example.com',
            'relationship': 'EXECUTOR'
        }
        file_data = {
            'death_certificate_file': self.test_file,
            'legal_documents': self.test_file
        }
        form = ProbateRequestForm(
            data=form_data,
            files=file_data
        )
        self.assertTrue(form.is_valid())

    def test_probate_request_form_missing_files(self):
        """Test probate request form without required files."""
        form_data = {
            'requestor_name': 'John Doe',
            'requestor_email': 'john@example.com',
            'relationship': 'EXECUTOR'
        }
        form = ProbateRequestForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('death_certificate_file', form.errors)

class ProbateReviewFormTest(TestCase):
    def test_probate_review_form_approve(self):
        """Test probate review form with approval."""
        form_data = {
            'decision': 'approve'
        }
        form = ProbateReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_probate_review_form_reject_without_reason(self):
        """Test probate review form rejection without reason."""
        form_data = {
            'decision': 'reject'
        }
        form = ProbateReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
```

### Step 4: View Tests

1. Create view tests
```python
# securemyassets/tests/test_views.py

from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from ..models import Asset, ProbateRequest
from .utils import (
    create_test_user,
    create_test_asset,
    create_test_probate_request,
    create_test_file
)

class AssetViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.client.login(
            username='testuser',
            password='testpass123'
        )

    def test_asset_list_view(self):
        """Test asset listing page."""
        # Create some test assets
        create_test_asset(self.user)
        create_test_asset(
            self.user,
            name='Asset 2',
            category='IDENTITY'
        )
        
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['assets']), 2)

    def test_asset_creation_view(self):
        """Test asset creation."""
        data = {
            'name': 'New Asset',
            'category': 'FINANCIAL',
            'note': 'Test note'
        }
        response = self.client.post(reverse('assets'), data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(
            Asset.objects.filter(name='New Asset').exists()
        )

    def test_asset_deletion_view(self):
        """Test asset deletion."""
        asset = create_test_asset(self.user)
        response = self.client.post(
            reverse('asset_delete', args=[asset.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Asset.objects.filter(pk=asset.pk).exists()
        )

class ProbateViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.staff = create_test_user(
            'staffuser',
            is_staff=True
        )
        self.test_file = create_test_file()

    def test_probate_request_submission(self):
        """Test probate request submission."""
        self.client.login(
            username='testuser',
            password='testpass123'
        )
        
        data = {
            'requestor_name': 'John Doe',
            'requestor_email': 'john@example.com',
            'relationship': 'EXECUTOR',
            'death_certificate_file': self.test_file,
            'legal_documents': self.test_file
        }
        
        response = self.client.post(
            reverse('submit_probate_request'),
            data
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProbateRequest.objects.exists())
        
        # Check email notification
        self.assertEqual(len(mail.outbox), 1)

    def test_probate_review_process(self):
        """Test probate review workflow."""
        self.client.login(
            username='staffuser',
            password='testpass123'
        )
        
        request = create_test_probate_request(self.user)
        
        # Test review listing
        response = self.client.get(
            reverse('review_probate_requests')
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(request, response.context['pending_requests'])
        
        # Test approval
        data = {'decision': 'approve'}
        response = self.client.post(
            reverse('review_probate_request', args=[request.pk]),
            data
        )
        self.assertEqual(response.status_code, 302)
        
        request.refresh_from_db()
        self.assertEqual(request.status, 'VERIFIED')
```

### Step 5: Security Tests

1. Create security-focused tests
```python
# securemyassets/tests/test_security.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import Asset, ProbateRequest
from .utils import create_test_user, create_test_asset

class SecurityTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = create_test_user('user1')
        self.user2 = create_test_user('user2')
        self.staff = create_test_user(
            'staffuser',
            is_staff=True
        )

    def test_asset_access_restrictions(self):
        """Test that users can only access their own assets."""
        # Create asset for user1
        asset = create_test_asset(self.user1)
        
        # Try accessing as user2
        self.client.login(
            username='user2',
            password='testpass123'
        )
        response = self.client.get(reverse('assets'))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(asset, response.context['assets'])

    def test_probate_review_restrictions(self):
        """Test that only staff can review probate requests."""
        request = create_test_probate_request(self.user1)
        
        # Try accessing as non-staff
        self.client.login(
            username='user1',
            password='testpass123'
        )
        response = self.client.get(
            reverse('review_probate_requests')
        )
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Try accessing as staff
        self.client.login(
            username='staffuser',
            password='testpass123'
        )
        response = self.client.get(
            reverse('review_probate_requests')
        )
        self.assertEqual(response.status_code, 200)

    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        self.client.login(
            username='user1',
            password='testpass123'
        )
        
        # Try posting without CSRF token
        self.client.handler.enforce_csrf_checks = True
        data = {
            'name': 'Test Asset',
            'category': 'FINANCIAL'
        }
        response = self.client.post(reverse('assets'), data)
        self.assertEqual(response.status_code, 403)

    def test_password_change_security(self):
        """Test password change security measures."""
        self.client.login(
            username='user1',
            password='testpass123'
        )
        
        # Try changing password
        data = {
            'old_password': 'testpass123',
            'new_password1': 'newpass123',
            'new_password2': 'newpass123'
        }
        response = self.client.post(
            reverse('password_change'),
            data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify old password no longer works
        self.client.logout()
        success = self.client.login(
            username='user1',
            password='testpass123'
        )
        self.assertFalse(success)
```

### Step 6: Integration Tests

1. Create integration tests
```python
# securemyassets/tests/test_integration.py

from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from ..models import Asset, ProbateRequest, ProbateAccess
from .utils import (
    create_test_user,
    create_test_asset,
    create_test_probate_request
)

class WorkflowIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = create_test_user()
        self.staff = create_test_user(
            'staffuser',
            is_staff=True
        )

    def test_complete_asset_workflow(self):
        """Test complete asset management workflow."""
        # Login
        self.client.login(
            username='testuser',
            password='testpass123'
        )
        
        # Create asset
        asset_data = {
            'name': 'Test Asset',
            'category': 'FINANCIAL',
            'note': 'Test note'
        }
        response = self.client.post(
            reverse('assets'),
            asset_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verify asset in listing
        response = self.client.get(reverse('assets'))
        self.assertContains(response, 'Test Asset')
        
        # Update asset
        asset = Asset.objects.first()
        update_data = {
            'name': 'Updated Asset',
            'category': 'FINANCIAL',
            'note': 'Updated note'
        }
        response = self.client.post(
            reverse('asset_edit', args=[asset.pk]),
            update_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Delete asset
        response = self.client.post(
            reverse('asset_delete', args=[asset.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Asset.objects.filter(pk=asset.pk).exists()
        )

    def test_complete_probate_workflow(self):
        """Test complete probate verification workflow."""
        # Create assets for deceased user
        asset1 = create_test_asset(self.user)
        asset2 = create_test_asset(
            self.user,
            name='Asset 2'
        )
        
        # Submit probate request
        request_data = {
            'requestor_name': 'John Doe',
            'requestor_email': 'john@example.com',
            'relationship': 'EXECUTOR',
            'death_certificate_file': create_test_file(),
            'legal_documents': create_test_file()
        }
        
        response = self.client.post(
            reverse('submit_probate_request'),
            request_data
        )
        self.assertEqual(response.status_code, 200)
        
        # Staff reviews request
        self.client.login(
            username='staffuser',
            password='testpass123'
        )
        
        request = ProbateRequest.objects.first()
        review_data = {'decision': 'approve'}
        
        response = self.client.post(
            reverse('review_probate_request', args=[request.pk]),
            review_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Check email notification
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Approved', mail.outbox[0].subject)
        
        # Access granted assets
        access = ProbateAccess.objects.first()
        response = self.client.get(
            reverse('probate_access', args=[access.access_token])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Asset 2')
```

### Step 7: Coverage Configuration

1. Create .coveragerc file
```ini
# .coveragerc

[run]
source = securemyassets/
omit =
    */migrations/*
    */tests/*
    */admin.py
    */apps.py
    */urls.py
    manage.py

[report]
exclude_lines =
    pragma: no cover
    def __str__
    raise NotImplementedError
    if __name__ == .__main__.:
    pass
    raise ImportError

[html]
directory = htmlcov
```

2. Add coverage commands to requirements.txt
```
# requirements.txt
coverage==7.3.2
```

### Step 8: GitHub Actions for Tests

1. Create GitHub Actions workflow
```yaml
# .github/workflows/tests.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests with coverage
      env:
        DATABASE_URL: postgres://postgres:postgres@localhost:5432/test_db
      run: |
        coverage run manage.py test
        coverage report
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: true
```

## Running Tests

To run the tests locally:

1. Run all tests
```bash
python manage.py test
```

2. Run tests with coverage
```bash
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

3. Run specific test cases
```bash
python manage.py test securemyassets.tests.test_models
python manage.py test securemyassets.tests.test_views.AssetViewsTest
```

## Next Steps
After completing this part, you should have:
- [x] Comprehensive test suite
- [x] Security testing
- [x] Integration testing
- [x] Coverage reporting
- [x] CI/CD setup

You can now proceed to Part 6: Deployment Process.

## Troubleshooting

### Common Testing Issues

1. Database Issues
   - Use `--keepdb` flag to preserve test database
   - Check database permissions
   - Verify migrations are up to date

2. Coverage Problems
   - Check .coveragerc configuration
   - Verify source paths
   - Clean old coverage data

3. Test Isolation Issues
   - Use `setUp` and `tearDown` properly
   - Clear cache between tests
   - Reset database state

### Best Practices
- Write tests before implementation (TDD)
- Keep tests focused and isolated
- Use meaningful test names
- Test edge cases
- Maintain test data fixtures
- Regular test runs
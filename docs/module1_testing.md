# Module 1: Django Testing Fundamentals

## Overview
This module covers Django testing fundamentals using our Digital Asset Security application as a practical example.

## 1. Test Structure

### Unit Test Basics
```python
from django.test import TestCase
from django.contrib.auth.models import User
from .models import Asset

class AssetModelTest(TestCase):
    def setUp(self):
        # Setup runs before each test method
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_asset_creation(self):
        # Test specific functionality
        asset = Asset.objects.create(
            user=self.user,
            name='Test Asset',
            category='FINANCIAL'
        )
        self.assertEqual(asset.name, 'Test Asset')
```

### Test Methods
1. `setUp()`: Runs before each test
2. `tearDown()`: Runs after each test
3. `setUpClass()`: Runs once before all tests
4. `tearDownClass()`: Runs once after all tests

## 2. Types of Tests

### Model Tests
Test data integrity and model methods:
```python
def test_str_representation(self):
    asset = Asset.objects.create(
        user=self.user,
        name='Test Asset',
        category='FINANCIAL'
    )
    self.assertEqual(str(asset), 'Financial - Test Asset')
```

### Form Tests
Validate form processing:
```python
from .forms import AssetForm

class AssetFormTest(TestCase):
    def test_valid_data(self):
        form = AssetForm({
            'name': 'Test Asset',
            'category': 'FINANCIAL',
            'note': 'Test note'
        })
        self.assertTrue(form.is_valid())
```

### View Tests
Test HTTP responses and logic:
```python
from django.urls import reverse

class ViewTests(TestCase):
    def test_dashboard_view(self):
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
```

## 3. Test Coverage

### Running Coverage
```bash
coverage run manage.py test
coverage report
coverage html  # Generate HTML report
```

### Coverage Configuration
```ini
[run]
source = securemyassets
omit = */migrations/*,*/tests/*
```

## 4. Test-Driven Development (TDD)

### TDD Cycle
1. Write a failing test
2. Write minimal code to pass
3. Refactor while keeping tests green

### Example TDD Process
```python
# 1. Write test first
def test_asset_category_validation(self):
    with self.assertRaises(ValidationError):
        asset = Asset(
            user=self.user,
            name='Test Asset',
            category='INVALID'
        )
        asset.full_clean()

# 2. Run test (should fail)
# 3. Implement validation
# 4. Run test again (should pass)
# 5. Refactor if needed
```

## 5. Testing Best Practices

1. Test Isolation
   - Each test should be independent
   - Use setUp/tearDown properly
   - Don't rely on test order

2. Meaningful Names
   ```python
   def test_asset_creation_with_valid_data():
   def test_asset_creation_fails_with_invalid_category():
   ```

3. Test Organization
   - Group related tests in classes
   - Use descriptive test class names
   - Follow naming conventions

4. Test Coverage Goals
   - Aim for 80%+ coverage
   - Focus on critical paths
   - Don't skip error cases

## 6. Common Testing Patterns

### Testing Files and Uploads
```python
from django.core.files.uploadedfile import SimpleUploadedFile

def test_pdf_upload():
    pdf = SimpleUploadedFile(
        "test.pdf",
        b"file_content",
        content_type="application/pdf"
    )
    form = ProbateUploadForm(files={'file': pdf})
    self.assertTrue(form.is_valid())
```

### Testing Authentication
```python
from django.contrib.auth.models import User

class AuthenticatedTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
```

### Testing Permissions
```python
def test_staff_required_view(self):
    # Test as regular user
    response = self.client.get(reverse('review_queue'))
    self.assertEqual(response.status_code, 403)
    
    # Test as staff
    self.user.is_staff = True
    self.user.save()
    response = self.client.get(reverse('review_queue'))
    self.assertEqual(response.status_code, 200)
```

## Exercises

1. Fix Form Validation Tests
   - Review Issue #1 in GitHub
   - Update form tests
   - Verify form validation logic

2. Fix View Redirect Tests
   - Review Issue #3 in GitHub
   - Check view response codes
   - Verify redirect chains

3. Fix Model String Tests
   - Review Issue #4 in GitHub
   - Update model string methods
   - Add new test cases

## Next Steps

1. Run the test suite
2. Check coverage report
3. Address failing tests
4. Add missing test cases
5. Document test patterns

Remember: Good tests make good code!
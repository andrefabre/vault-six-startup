from django.test import TestCase
from django.contrib.auth.models import User
from securemyassets.forms import SignUpForm, AssetForm, ProbateUploadForm
from django.core.files.uploadedfile import SimpleUploadedFile

class SignUpFormTest(TestCase):
    def test_valid_signup_form(self):
        """Test that form is valid with correct data"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_password_match(self):
        """Test that form is invalid when passwords don't match"""
        form_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'securepass123',
            'password2': 'differentpass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_invalid_email(self):
        """Test that form is invalid with incorrect email format"""
        form_data = {
            'username': 'testuser',
            'email': 'invalid-email',
            'password1': 'securepass123',
            'password2': 'securepass123'
        }
        form = SignUpForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

class AssetFormTest(TestCase):
    def test_valid_asset_form(self):
        """Test that form is valid with correct data"""
        form_data = {
            'name': 'Test Asset',
            'category': 'SOCIAL',
            'note': 'Test note'
        }
        form = AssetForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_category(self):
        """Test that form is invalid with incorrect category"""
        form_data = {
            'name': 'Test Asset',
            'category': 'INVALID',
            'note': 'Test note'
        }
        form = AssetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('category', form.errors)

    def test_empty_name(self):
        """Test that form is invalid with empty name"""
        form_data = {
            'name': '',
            'category': 'SOCIAL',
            'note': 'Test note'
        }
        form = AssetForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)

class ProbateUploadFormTest(TestCase):
    def test_valid_probate_upload_form(self):
        """Test that form is valid with correct file"""
        dummy_pdf = SimpleUploadedFile(
            "test.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        form = ProbateUploadForm(files={'document': dummy_pdf})
        self.assertTrue(form.is_valid())

    def test_invalid_file_type(self):
        """Test that form is invalid with non-PDF file"""
        dummy_file = SimpleUploadedFile(
            "test.txt",
            b"file_content",
            content_type="text/plain"
        )
        form = ProbateUploadForm(files={'document': dummy_file})
        self.assertFalse(form.is_valid())
        self.assertIn('document', form.errors)

    def test_empty_form(self):
        """Test that form is invalid without file"""
        form = ProbateUploadForm(files={})
        self.assertFalse(form.is_valid())
        self.assertIn('document', form.errors)
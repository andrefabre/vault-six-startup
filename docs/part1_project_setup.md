# Part 1: Project Setup and Environment Configuration

## Detailed Step-by-Step Guide

### Step 1: Initial Repository Setup

1. Create new GitHub repository
   - Go to GitHub.com
   - Click "New repository"
   - Name: vault-six-startup-demo
   - Add Description: "Digital Asset Security Application"
   - Initialize with README.md
   - Add .gitignore (Python template)
   - License: MIT

2. Clone repository locally
   ```bash
   git clone https://github.com/[your-username]/vault-six-startup-demo.git
   cd vault-six-startup-demo
   ```

3. Set up Python virtual environment
   ```bash
   # Create virtual environment
   python -m venv venv
   # Activate virtual environment
   # On Windows:
   .\venv\Scripts\Activate.ps1
   # On Unix/MacOS:
   source venv/bin/activate
   ```

4. Install required packages
   ```bash
   pip install django==5.2.6
   pip install django-crispy-forms==2.1
   pip install crispy-bootstrap4==2023.1
   pip install django-jazzmin==2.6.0
   pip install python-magic-bin==0.4.14
   
   # Save requirements
   pip freeze > requirements.txt
   ```

### Step 2: Django Project Setup

1. Create Django project
   ```bash
   django-admin startproject DigitalAssetSecurity .
   ```

2. Create main application
   ```bash
   python manage.py startapp securemyassets
   ```

3. Create project structure
   ```bash
   mkdir securemyassets/templates
   mkdir securemyassets/templates/app
   mkdir securemyassets/templates/registration
   mkdir securemyassets/static
   mkdir securemyassets/static/css
   mkdir securemyassets/static/js
   mkdir securemyassets/tests
   mkdir securemyassets/management
   mkdir securemyassets/management/commands
   ```

4. Update settings.py
   ```python
   # DigitalAssetSecurity/settings.py
   
   INSTALLED_APPS = [
       'jazzmin',  # Add before django.contrib.admin
       'django.contrib.admin',
       'django.contrib.auth',
       'django.contrib.contenttypes',
       'django.contrib.sessions',
       'django.contrib.messages',
       'django.contrib.staticfiles',
       'crispy_forms',
       'crispy_bootstrap4',
       'securemyassets',
   ]

   CRISPY_TEMPLATE_PACK = 'bootstrap4'
   CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap4"

   # Media files configuration
   MEDIA_URL = '/media/'
   MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

   # Authentication settings
   LOGIN_REDIRECT_URL = 'dashboard'
   LOGOUT_REDIRECT_URL = 'home'
   LOGIN_URL = 'login'

   # Jazzmin settings
   JAZZMIN_SETTINGS = {
       "site_title": "Digital Asset Security Admin",
       "site_header": "Digital Asset Security",
       "site_brand": "Digital Asset Security",
       "welcome_sign": "Welcome to the Digital Asset Security Portal",
       "copyright": "Digital Asset Security Ltd",
   }
   ```

5. Update base URLs
   ```python
   # DigitalAssetSecurity/urls.py
   
   from django.contrib import admin
   from django.urls import path, include
   from django.conf import settings
   from django.conf.urls.static import static

   urlpatterns = [
       path('admin/', admin.site.urls),
       path('', include('securemyassets.urls')),
   ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
   ```

### Step 3: Initial Models Setup

1. Create base models
   ```python
   # securemyassets/models.py
   
   from django.db import models
   from django.contrib.auth.models import User
   from django.core.exceptions import ValidationError
   import magic
   import os

   def validate_pdf_file(value):
       # Check file extension
       ext = os.path.splitext(value.name)[1]
       if ext.lower() != '.pdf':
           raise ValidationError('Only PDF files are allowed.')
       
       # Check MIME type
       file_mime = magic.from_buffer(value.read(1024), mime=True)
       if file_mime != 'application/pdf':
           raise ValidationError('File is not a valid PDF.')
       
       # Reset file pointer
       value.seek(0)
       
       # Check file size (2MB limit)
       if value.size > 2 * 1024 * 1024:
           raise ValidationError('File size must be under 2MB.')

   class Asset(models.Model):
       CATEGORY_CHOICES = [
           ('IDENTITY', 'Identity'),
           ('FINANCIAL', 'Financial'),
           ('DEVICES', 'Digital Devices'),
           ('CONTENT', 'Digital Content, Services and Storage'),
           ('LEGAL', 'Legal'),
           ('HEALTH', 'Health and Wellness'),
           ('BUSINESS', 'Business'),
       ]
       
       category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
       name = models.CharField(max_length=100)
       note = models.TextField(blank=True)
       user = models.ForeignKey(User, on_delete=models.CASCADE)
       created_at = models.DateTimeField(auto_now_add=True)
       updated_at = models.DateTimeField(auto_now=True)

       class Meta:
           ordering = ['category', 'name']
           
       def __str__(self):
           return f'{self.get_category_display()} - {self.name}'

   class ProbateGrant(models.Model):
       STATUS_CHOICES = [
           ('UPLOADED', 'Uploaded'),
           ('APPROVED', 'Approved'),
           ('REJECTED', 'Rejected'),
       ]
       
       user = models.ForeignKey(User, on_delete=models.CASCADE)
       file = models.FileField(
           upload_to='probate_docs/',
           validators=[validate_pdf_file]
       )
       status = models.CharField(
           max_length=10,
           choices=STATUS_CHOICES,
           default='UPLOADED'
       )
       created_at = models.DateTimeField(auto_now_add=True)
       reviewed_at = models.DateTimeField(null=True, blank=True)
       reviewed_by = models.ForeignKey(
           User,
           on_delete=models.SET_NULL,
           null=True,
           blank=True,
           related_name='reviewed_grants'
       )
       review_notes = models.TextField(blank=True)

       def __str__(self):
           return f'Probate Grant for {self.user.username}'

   class VaultAccess(models.Model):
       user = models.OneToOneField(User, on_delete=models.CASCADE)
       granted = models.BooleanField(default=False)
       granted_at = models.DateTimeField(null=True, blank=True)
       
       def __str__(self):
           return f'Vault access for {self.user.username}'
   ```

2. Register models in admin
   ```python
   # securemyassets/admin.py
   
   from django.contrib import admin
   from .models import Asset, ProbateGrant, VaultAccess

   @admin.register(Asset)
   class AssetAdmin(admin.ModelAdmin):
       list_display = ('name', 'category', 'user', 'created_at')
       list_filter = ('category', 'user')
       search_fields = ('name', 'note')
       date_hierarchy = 'created_at'

   @admin.register(ProbateGrant)
   class ProbateGrantAdmin(admin.ModelAdmin):
       list_display = ('user', 'status', 'created_at', 'reviewed_by')
       list_filter = ('status',)
       date_hierarchy = 'created_at'

   @admin.register(VaultAccess)
   class VaultAccessAdmin(admin.ModelAdmin):
       list_display = ('user', 'granted', 'granted_at')
       list_filter = ('granted',)
   ```

3. Create and apply migrations
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. Create superuser
   ```bash
   python manage.py createsuperuser
   ```

### Step 4: Verify Setup

1. Run development server
   ```bash
   python manage.py runserver
   ```

2. Access admin interface
   - Go to http://127.0.0.1:8000/admin/
   - Login with superuser credentials
   - Verify models are visible in admin

3. Commit changes
   ```bash
   git add .
   git commit -m "Initial project setup with models and admin configuration"
   git push origin main
   ```

## Next Steps
After completing this setup, you're ready to move on to Part 2: Authentication and User Management.

### Checkpoint
Verify that you have:
- [ ] Working Django project
- [ ] Virtual environment with all dependencies
- [ ] Models created and migrated
- [ ] Admin interface accessible
- [ ] All changes committed to GitHub

If any of these are not working, review the steps before proceeding.
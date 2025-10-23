# Part 2: Authentication and User Management

## Overview
In this part, we'll implement user authentication, registration, and permission management. We'll create forms for user signup, implement login/logout functionality, and set up staff-specific features.

## Step-by-Step Implementation

### Step 1: Create Authentication Forms

1. Create forms.py
```python
# securemyassets/forms.py

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class SignUpForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='Required. Enter a valid email address.'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email
```

### Step 2: Create Authentication Templates

1. Create base template
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Digital Asset Security{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'home' %}">Digital Asset Security</a>
            <button class="navbar-toggler" type="button" data-toggle="collapse" data-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav ml-auto">
                    {% if user.is_authenticated %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'dashboard' %}">Dashboard</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'assets' %}">Assets</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'requests' %}">Requests</a>
                        </li>
                        {% if user.is_staff %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'review_queue' %}">Review Queue</a>
                        </li>
                        {% endif %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'logout' %}">Logout</a>
                        </li>
                    {% else %}
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'login' %}">Login</a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="{% url 'signup' %}">Sign Up</a>
                        </li>
                    {% endif %}
                </ul>
            </div>
        </div>
    </nav>

    <div class="container mt-4">
        {% if messages %}
            {% for message in messages %}
                <div class="alert alert-{{ message.tags }} alert-dismissible fade show">
                    {{ message }}
                    <button type="button" class="close" data-dismiss="alert">
                        <span>&times;</span>
                    </button>
                </div>
            {% endfor %}
        {% endif %}

        {% block content %}{% endblock %}
    </div>

    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
```

2. Create login template
```html
<!-- templates/registration/login.html -->
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Login - Digital Asset Security{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow">
            <div class="card-body">
                <h2 class="card-title text-center mb-4">Login</h2>
                <form method="post">
                    {% csrf_token %}
                    {{ form|crispy }}
                    <button type="submit" class="btn btn-primary btn-block">Login</button>
                </form>
                <div class="text-center mt-3">
                    <p>Don't have an account? <a href="{% url 'signup' %}">Sign Up</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

3. Create signup template
```html
<!-- templates/registration/signup.html -->
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Sign Up - Digital Asset Security{% endblock %}

{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow">
            <div class="card-body">
                <h2 class="card-title text-center mb-4">Sign Up</h2>
                <form method="post">
                    {% csrf_token %}
                    {{ form|crispy }}
                    <button type="submit" class="btn btn-primary btn-block">Sign Up</button>
                </form>
                <div class="text-center mt-3">
                    <p>Already have an account? <a href="{% url 'login' %}">Login</a></p>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 3: Create Authentication Views

1. Update views.py
```python
# securemyassets/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import SignUpForm

def home(request):
    """Landing page view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'app/home.html')

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create VaultAccess record for new user
            VaultAccess.objects.create(user=user)
            login(request, user)
            messages.success(request, 'Welcome! Your account has been created successfully.')
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})

def staff_required(function):
    """Decorator for views that checks if the user is staff."""
    actual_decorator = user_passes_test(lambda u: u.is_staff)
    return actual_decorator(function)
```

### Step 4: Update URL Configuration

1. Update urls.py
```python
# securemyassets/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]
```

### Step 5: Create Management Command for Staff Users

1. Create command file
```python
# securemyassets/management/commands/create_staff_user.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Creates a staff user for testing and review functionality'

    def handle(self, *args, **options):
        username = 'reviewer'
        email = 'reviewer@example.com'
        password = 'reviewpass123'

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING('Staff user already exists'))
            return

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            is_staff=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'''Successfully set up staff user:
                Username: {username}
                Password: {password}
                Email: {email}
                Staff Status: {user.is_staff}'''
            )
        )
```

### Step 6: Test Authentication System

1. Run the development server
```bash
python manage.py runserver
```

2. Test user registration
- Visit http://127.0.0.1:8000/signup/
- Create a new account
- Verify VaultAccess record is created

3. Test staff user creation
```bash
python manage.py create_staff_user
```

4. Test login/logout functionality
- Login with both regular and staff users
- Verify proper navigation menu items
- Test logout functionality

### Step 7: Add Authentication Tests

1. Create authentication tests
```python
# securemyassets/tests/test_auth.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from securemyassets.models import VaultAccess

class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.dashboard_url = reverse('dashboard')

    def test_signup_view(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_creates_vault_access(self):
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
        }
        response = self.client.post(self.signup_url, data)
        self.assertRedirects(response, self.dashboard_url)
        
        # Check user was created
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_active)
        
        # Check VaultAccess was created
        vault_access = VaultAccess.objects.get(user=user)
        self.assertFalse(vault_access.granted)

    def test_login_redirect(self):
        # Create a user
        user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Try to access dashboard before login
        response = self.client.get(self.dashboard_url)
        self.assertRedirects(
            response,
            f'{self.login_url}?next={self.dashboard_url}'
        )
        
        # Login and try again
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)
```

## Next Steps
After completing this part, you should have:
- [x] Working user registration
- [x] Login/logout functionality
- [x] Staff user management
- [x] Basic permission system
- [x] Authentication tests

You can now proceed to Part 3: Asset Management Implementation.

## Troubleshooting

### Common Issues

1. Login not working
   - Check settings.py for LOGIN_REDIRECT_URL
   - Verify password meets complexity requirements
   - Check for proper template paths

2. Staff permissions not working
   - Verify user.is_staff is True
   - Check staff_required decorator usage
   - Verify template conditions for staff-only content

3. VaultAccess not created
   - Check signup view for VaultAccess creation
   - Verify signals if using them
   - Check database migrations

### Testing Tips
- Use test client for authentication tests
- Test both valid and invalid credentials
- Verify proper redirect chains
- Check permission-protected views
- Test staff vs regular user access
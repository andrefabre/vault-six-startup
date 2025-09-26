# Part 3: Asset Management Implementation

## Overview
In this part, we'll implement the core asset management functionality, including:
- Asset creation and management
- Asset categorization
- Asset listing and filtering
- Asset deletion with confirmation

## Step-by-Step Implementation

### Step 1: Create Asset Forms

1. Update forms.py with Asset form
```python
# securemyassets/forms.py

from django import forms
from .models import Asset

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'category', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].help_text = 'Select the most appropriate category for your digital asset.'
        self.fields['note'].help_text = 'Add any relevant details or access information.'
```

### Step 2: Create Asset Templates

1. Create assets list template
```html
<!-- templates/app/assets.html -->
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}My Assets - Digital Asset Security{% endblock %}

{% block content %}
<div class="row">
    <!-- Asset List -->
    <div class="col-md-8">
        <div class="card shadow">
            <div class="card-body">
                <h4 class="card-title">My Digital Assets</h4>
                {% if assets %}
                    <div class="table-responsive">
                        <table class="table">
                            <thead>
                                <tr>
                                    <th>Category</th>
                                    <th>Name</th>
                                    <th>Note</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for asset in assets %}
                                    <tr>
                                        <td>{{ asset.get_category_display }}</td>
                                        <td>{{ asset.name }}</td>
                                        <td>{{ asset.note|truncatewords:10 }}</td>
                                        <td>
                                            <form method="post" action="{% url 'asset_delete' asset.pk %}" class="d-inline">
                                                {% csrf_token %}
                                                <button type="submit" class="btn btn-danger btn-sm" 
                                                        onclick="return confirm('Are you sure you want to delete this asset?')">
                                                    Delete
                                                </button>
                                            </form>
                                        </td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                {% else %}
                    <p class="text-muted">No assets added yet.</p>
                {% endif %}
            </div>
        </div>
    </div>

    <!-- Add Asset Form -->
    <div class="col-md-4">
        <div class="card shadow">
            <div class="card-body">
                <h4 class="card-title">Add New Asset</h4>
                <form method="post">
                    {% csrf_token %}
                    {{ form|crispy }}
                    <button type="submit" class="btn btn-primary btn-block">Add Asset</button>
                </form>
            </div>
        </div>
    </div>
</div>

<!-- Category Filter Modal -->
<div class="modal fade" id="filterModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Filter Assets</h5>
                <button type="button" class="close" data-dismiss="modal">
                    <span>&times;</span>
                </button>
            </div>
            <div class="modal-body">
                <form method="get">
                    <div class="form-group">
                        <label>Category</label>
                        <select name="category" class="form-control">
                            <option value="">All Categories</option>
                            {% for value, label in Asset.CATEGORY_CHOICES %}
                                <option value="{{ value }}" {% if selected_category == value %}selected{% endif %}>
                                    {{ label }}
                                </option>
                            {% endfor %}
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">Apply Filter</button>
                    {% if selected_category %}
                        <a href="{% url 'assets' %}" class="btn btn-secondary">Clear Filter</a>
                    {% endif %}
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 3: Update Views

1. Add asset views to views.py
```python
# securemyassets/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Asset
from .forms import AssetForm

@login_required
def assets(request):
    # Handle new asset form
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.user = request.user
            asset.save()
            messages.success(request, 'Asset added successfully!')
            return redirect('assets')
    else:
        form = AssetForm()
    
    # Get filter parameters
    category = request.GET.get('category')
    
    # Filter assets
    assets = Asset.objects.filter(user=request.user)
    if category:
        assets = assets.filter(category=category)
    assets = assets.order_by('category', 'name')
    
    context = {
        'assets': assets,
        'form': form,
        'Asset': Asset,  # For category choices in template
        'selected_category': category,
    }
    return render(request, 'app/assets.html', context)

@login_required
def asset_delete(request, pk):
    asset = get_object_or_404(Asset, pk=pk, user=request.user)
    if request.method == 'POST':
        asset.delete()
        messages.success(request, 'Asset deleted successfully!')
    return redirect('assets')
```

2. Update URLs
```python
# securemyassets/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # ... existing URLs ...
    path('assets/', views.assets, name='assets'),
    path('asset/delete/<int:pk>/', views.asset_delete, name='asset_delete'),
]
```

### Step 4: Add Asset Category Icons

1. Create template tag for category icons
```python
# securemyassets/templatetags/asset_tags.py

from django import template

register = template.Library()

@register.filter
def category_icon(category):
    icons = {
        'IDENTITY': 'fa-id-card',
        'FINANCIAL': 'fa-money-bill-wave',
        'DEVICES': 'fa-laptop',
        'CONTENT': 'fa-cloud',
        'LEGAL': 'fa-balance-scale',
        'HEALTH': 'fa-heartbeat',
        'BUSINESS': 'fa-briefcase',
    }
    return icons.get(category, 'fa-question-circle')
```

2. Update assets template to use icons
```html
<!-- In assets.html, update the category column -->
<td>
    <i class="fas {{ asset.category|category_icon }} mr-2"></i>
    {{ asset.get_category_display }}
</td>
```

### Step 5: Add Asset Tests

1. Create asset tests
```python
# securemyassets/tests/test_assets.py

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from securemyassets.models import Asset

class AssetManagementTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.assets_url = reverse('assets')
        
        # Create test asset
        self.asset = Asset.objects.create(
            user=self.user,
            name='Test Asset',
            category='FINANCIAL',
            note='Test note'
        )

    def test_asset_list_view(self):
        response = self.client.get(self.assets_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'app/assets.html')
        self.assertContains(response, 'Test Asset')

    def test_asset_creation(self):
        data = {
            'name': 'New Asset',
            'category': 'IDENTITY',
            'note': 'New note'
        }
        response = self.client.post(self.assets_url, data)
        self.assertRedirects(response, self.assets_url)
        self.assertTrue(
            Asset.objects.filter(name='New Asset', user=self.user).exists()
        )

    def test_asset_deletion(self):
        response = self.client.post(
            reverse('asset_delete', args=[self.asset.pk])
        )
        self.assertRedirects(response, self.assets_url)
        self.assertFalse(
            Asset.objects.filter(pk=self.asset.pk).exists()
        )

    def test_asset_category_filter(self):
        # Create assets in different categories
        Asset.objects.create(
            user=self.user,
            name='Identity Asset',
            category='IDENTITY'
        )
        
        # Test filtering
        response = self.client.get(f'{self.assets_url}?category=FINANCIAL')
        self.assertContains(response, 'Test Asset')
        self.assertNotContains(response, 'Identity Asset')
```

### Step 6: Add Asset Management to Dashboard

1. Update dashboard template to show asset summary
```html
<!-- templates/app/dashboard.html -->
<!-- Add this section -->
<div class="col-md-12">
    <div class="card shadow">
        <div class="card-body">
            <h4 class="card-title">Asset Summary</h4>
            <div class="row">
                {% for category, count in asset_counts.items %}
                <div class="col-md-3 mb-3">
                    <div class="card bg-light">
                        <div class="card-body text-center">
                            <i class="fas {{ category|category_icon }} fa-2x mb-2"></i>
                            <h5>{{ category }}</h5>
                            <p class="mb-0">{{ count }} assets</p>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
            <div class="text-right mt-3">
                <a href="{% url 'assets' %}" class="btn btn-primary">Manage Assets</a>
            </div>
        </div>
    </div>
</div>
```

2. Update dashboard view to include asset counts
```python
@login_required
def dashboard(request):
    # Get asset counts by category
    asset_counts = {}
    for category, label in Asset.CATEGORY_CHOICES:
        count = Asset.objects.filter(
            user=request.user,
            category=category
        ).count()
        if count > 0:  # Only show categories with assets
            asset_counts[label] = count
    
    context = {
        'asset_counts': asset_counts,
        # ... other context data ...
    }
    return render(request, 'app/dashboard.html', context)
```

## Next Steps
After completing this part, you should have:
- [x] Working asset management system
- [x] Asset categorization and filtering
- [x] Asset creation and deletion
- [x] Dashboard integration
- [x] Comprehensive tests

You can now proceed to Part 4: Probate Verification System.

## Troubleshooting

### Common Issues

1. Assets not showing up
   - Check user authentication in view
   - Verify asset ownership filtering
   - Check template for-loop structure

2. Category filtering not working
   - Verify URL parameters
   - Check filter logic in view
   - Validate category choices

3. Delete confirmation not working
   - Check JavaScript confirmation dialog
   - Verify CSRF token in form
   - Check URL pattern matching

### Testing Tips
- Test asset creation with all categories
- Verify asset ownership separation
- Test filter combinations
- Validate deletion protection
- Check dashboard summary accuracy
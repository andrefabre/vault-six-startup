# Part 4: Probate Verification System

## Overview
The Probate Verification System is a critical security feature that ensures digital assets are accessible to authorized beneficiaries after proper legal verification. This part covers:
- Probate request submission
- Document verification workflow
- Legal representative authentication
- Access grant management

## Step-by-Step Implementation

### Step 1: Create Probate Models

1. Add probate models to models.py
```python
# securemyassets/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class ProbateRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('VERIFIED', 'Documents Verified'),
        ('GRANTED', 'Access Granted'),
        ('REJECTED', 'Request Rejected'),
    ]

    deceased_user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='probate_requests'
    )
    requestor_name = models.CharField(max_length=255)
    requestor_email = models.EmailField()
    relationship = models.CharField(max_length=100)
    death_certificate_file = models.FileField(
        upload_to='probate_docs/%Y/%m/',
        null=True,
        blank=True
    )
    legal_documents = models.FileField(
        upload_to='probate_docs/%Y/%m/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reviewed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_requests'
    )
    review_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Probate Request for {self.deceased_user.username}"

    def approve(self, reviewer):
        self.status = 'VERIFIED'
        self.reviewed_by = reviewer
        self.review_date = timezone.now()
        self.save()

    def reject(self, reviewer, reason):
        self.status = 'REJECTED'
        self.reviewed_by = reviewer
        self.review_date = timezone.now()
        self.notes = reason
        self.save()

    def grant_access(self):
        if self.status == 'VERIFIED':
            self.status = 'GRANTED'
            self.save()
            return True
        return False

class ProbateAccess(models.Model):
    probate_request = models.OneToOneField(
        ProbateRequest,
        on_delete=models.PROTECT
    )
    access_token = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    last_accessed = models.DateTimeField(null=True, blank=True)

    def is_valid(self):
        return self.expires_at > timezone.now()

    def record_access(self):
        self.last_accessed = timezone.now()
        self.save()
```

### Step 2: Create Probate Forms

1. Add forms for probate requests
```python
# securemyassets/forms.py

from django import forms
from .models import ProbateRequest

class ProbateRequestForm(forms.ModelForm):
    class Meta:
        model = ProbateRequest
        fields = [
            'requestor_name',
            'requestor_email',
            'relationship',
            'death_certificate_file',
            'legal_documents'
        ]
        widgets = {
            'relationship': forms.Select(choices=[
                ('EXECUTOR', 'Estate Executor'),
                ('ATTORNEY', 'Attorney'),
                ('FAMILY', 'Family Member'),
                ('OTHER', 'Other')
            ])
        }

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('death_certificate_file'):
            raise forms.ValidationError(
                "Death certificate is required for verification."
            )
        return cleaned_data

class ProbateReviewForm(forms.Form):
    decision = forms.ChoiceField(choices=[
        ('approve', 'Approve Request'),
        ('reject', 'Reject Request')
    ])
    rejection_reason = forms.CharField(
        widget=forms.Textarea,
        required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        if (cleaned_data.get('decision') == 'reject' and
            not cleaned_data.get('rejection_reason')):
            raise forms.ValidationError(
                "Rejection reason is required when rejecting a request."
            )
        return cleaned_data
```

### Step 3: Create Probate Views

1. Add views for handling probate requests
```python
# securemyassets/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from .models import ProbateRequest, ProbateAccess
from .forms import ProbateRequestForm, ProbateReviewForm

def is_staff(user):
    return user.is_staff

def submit_probate_request(request):
    if request.method == 'POST':
        form = ProbateRequestForm(request.POST, request.FILES)
        if form.is_valid():
            probate_request = form.save(commit=False)
            probate_request.deceased_user = request.user
            probate_request.save()
            
            # Notify staff
            notify_staff_new_request(probate_request)
            
            return render(request, 'app/probate_submitted.html')
    else:
        form = ProbateRequestForm()
    
    return render(request, 'app/probate_request.html', {'form': form})

@user_passes_test(is_staff)
def review_probate_requests(request):
    pending_requests = ProbateRequest.objects.filter(
        status='PENDING'
    ).order_by('created_at')
    
    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'app/probate_review_list.html', context)

@user_passes_test(is_staff)
def review_probate_request(request, request_id):
    probate_request = get_object_or_404(ProbateRequest, pk=request_id)
    
    if request.method == 'POST':
        form = ProbateReviewForm(request.POST)
        if form.is_valid():
            decision = form.cleaned_data['decision']
            
            if decision == 'approve':
                probate_request.approve(request.user)
                create_probate_access(probate_request)
                notify_requestor_approved(probate_request)
            else:
                reason = form.cleaned_data['rejection_reason']
                probate_request.reject(request.user, reason)
                notify_requestor_rejected(probate_request)
            
            return redirect('review_probate_requests')
    else:
        form = ProbateReviewForm()
    
    context = {
        'probate_request': probate_request,
        'form': form,
    }
    return render(request, 'app/probate_review.html', context)

def probate_access(request, token):
    access = get_object_or_404(
        ProbateAccess,
        access_token=token
    )
    
    if not access.is_valid():
        return render(request, 'app/probate_access_expired.html')
    
    access.record_access()
    assets = Asset.objects.filter(user=access.probate_request.deceased_user)
    
    context = {
        'deceased_user': access.probate_request.deceased_user,
        'assets': assets,
    }
    return render(request, 'app/probate_assets.html', context)

# Helper functions
def create_probate_access(probate_request):
    token = get_random_string(64)
    expires_at = timezone.now() + timedelta(days=30)
    
    ProbateAccess.objects.create(
        probate_request=probate_request,
        access_token=token,
        expires_at=expires_at
    )

def notify_staff_new_request(probate_request):
    subject = 'New Probate Request Submitted'
    message = render_to_string('emails/new_probate_request.html', {
        'request': probate_request
    })
    send_mail(
        subject,
        message,
        None,  # From email (uses DEFAULT_FROM_EMAIL)
        [user.email for user in User.objects.filter(is_staff=True)],
        html_message=message
    )

def notify_requestor_approved(probate_request):
    access = probate_request.probateaccess
    subject = 'Probate Request Approved'
    message = render_to_string('emails/probate_approved.html', {
        'request': probate_request,
        'access_token': access.access_token,
        'expires_at': access.expires_at
    })
    send_mail(
        subject,
        message,
        None,
        [probate_request.requestor_email],
        html_message=message
    )

def notify_requestor_rejected(probate_request):
    subject = 'Probate Request Update'
    message = render_to_string('emails/probate_rejected.html', {
        'request': probate_request
    })
    send_mail(
        subject,
        message,
        None,
        [probate_request.requestor_email],
        html_message=message
    )
```

### Step 4: Create Probate Templates

1. Create template for probate request form
```html
<!-- templates/app/probate_request.html -->
{% extends 'base.html' %}
{% load crispy_forms_tags %}

{% block title %}Submit Probate Request{% endblock %}

{% block content %}
<div class="container">
    <div class="row justify-content-center">
        <div class="col-md-8">
            <div class="card shadow">
                <div class="card-body">
                    <h3 class="card-title">Submit Probate Request</h3>
                    <p class="text-muted">
                        Please provide the required information and documentation
                        to verify your legal right to access these digital assets.
                    </p>
                    
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        {{ form|crispy }}
                        
                        <div class="alert alert-info">
                            <h5>Required Documents:</h5>
                            <ul>
                                <li>Death Certificate</li>
                                <li>Proof of legal authority (e.g., Letters Testamentary)</li>
                            </ul>
                        </div>
                        
                        <button type="submit" class="btn btn-primary">
                            Submit Request
                        </button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

2. Create template for staff review list
```html
<!-- templates/app/probate_review_list.html -->
{% extends 'base.html' %}

{% block title %}Review Probate Requests{% endblock %}

{% block content %}
<div class="container">
    <div class="card shadow">
        <div class="card-body">
            <h3 class="card-title">Pending Probate Requests</h3>
            
            {% if pending_requests %}
                <div class="table-responsive">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Deceased User</th>
                                <th>Requestor</th>
                                <th>Relationship</th>
                                <th>Submitted</th>
                                <th>Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for request in pending_requests %}
                                <tr>
                                    <td>{{ request.deceased_user.username }}</td>
                                    <td>{{ request.requestor_name }}</td>
                                    <td>{{ request.get_relationship_display }}</td>
                                    <td>{{ request.created_at|date }}</td>
                                    <td>
                                        <a href="{% url 'review_probate_request' request.pk %}"
                                           class="btn btn-primary btn-sm">
                                            Review
                                        </a>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            {% else %}
                <p class="text-muted">No pending requests.</p>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

### Step 5: Add Email Templates

1. Create email templates for notifications
```html
<!-- templates/emails/new_probate_request.html -->
<h2>New Probate Request Submitted</h2>
<p>A new probate request has been submitted for review:</p>
<ul>
    <li><strong>Deceased User:</strong> {{ request.deceased_user.username }}</li>
    <li><strong>Requestor:</strong> {{ request.requestor_name }}</li>
    <li><strong>Relationship:</strong> {{ request.get_relationship_display }}</li>
    <li><strong>Submitted:</strong> {{ request.created_at|date }}</li>
</ul>
<p>
    <a href="{{ site_url }}{% url 'review_probate_request' request.pk %}">
        Review Request
    </a>
</p>
```

```html
<!-- templates/emails/probate_approved.html -->
<h2>Probate Request Approved</h2>
<p>Your probate request has been approved. You can now access the digital assets using the following link:</p>
<p>
    <a href="{{ site_url }}{% url 'probate_access' access_token %}">
        Access Digital Assets
    </a>
</p>
<p>This link will expire on {{ expires_at|date }}.</p>
```

### Step 6: Add Tests

1. Create tests for probate functionality
```python
# securemyassets/tests/test_probate.py

from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from ..models import ProbateRequest, ProbateAccess
from datetime import timedelta

class ProbateSystemTest(TestCase):
    def setUp(self):
        self.client = Client()
        # Create staff user
        self.staff_user = User.objects.create_user(
            username='staffuser',
            password='staffpass123',
            is_staff=True
        )
        # Create regular user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Create test files
        self.death_cert = SimpleUploadedFile(
            "death_cert.pdf",
            b"file_content",
            content_type="application/pdf"
        )
        self.legal_doc = SimpleUploadedFile(
            "legal_doc.pdf",
            b"file_content",
            content_type="application/pdf"
        )

    def test_probate_request_submission(self):
        self.client.login(username='testuser', password='testpass123')
        
        data = {
            'requestor_name': 'John Doe',
            'requestor_email': 'john@example.com',
            'relationship': 'EXECUTOR',
            'death_certificate_file': self.death_cert,
            'legal_documents': self.legal_doc
        }
        
        response = self.client.post(reverse('submit_probate_request'), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProbateRequest.objects.exists())
        
        # Check if staff was notified
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'New Probate Request Submitted'
        )

    def test_probate_review_process(self):
        # Create a probate request
        request = ProbateRequest.objects.create(
            deceased_user=self.user,
            requestor_name='John Doe',
            requestor_email='john@example.com',
            relationship='EXECUTOR',
            status='PENDING'
        )
        
        # Login as staff
        self.client.login(username='staffuser', password='staffpass123')
        
        # Approve request
        data = {
            'decision': 'approve'
        }
        response = self.client.post(
            reverse('review_probate_request', args=[request.pk]),
            data
        )
        
        # Check if request was approved
        request.refresh_from_db()
        self.assertEqual(request.status, 'VERIFIED')
        self.assertTrue(hasattr(request, 'probateaccess'))
        
        # Check if requestor was notified
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            mail.outbox[0].subject,
            'Probate Request Approved'
        )

    def test_probate_access(self):
        # Create approved request with access
        request = ProbateRequest.objects.create(
            deceased_user=self.user,
            requestor_name='John Doe',
            requestor_email='john@example.com',
            relationship='EXECUTOR',
            status='VERIFIED'
        )
        
        access = ProbateAccess.objects.create(
            probate_request=request,
            access_token='testtoken123',
            expires_at=timezone.now() + timedelta(days=30)
        )
        
        # Test access with valid token
        response = self.client.get(
            reverse('probate_access', args=[access.access_token])
        )
        self.assertEqual(response.status_code, 200)
        
        # Test access with expired token
        access.expires_at = timezone.now() - timedelta(days=1)
        access.save()
        
        response = self.client.get(
            reverse('probate_access', args=[access.access_token])
        )
        self.assertTemplateUsed(response, 'app/probate_access_expired.html')
```

## Next Steps
After completing this part, you should have:
- [x] Complete probate request system
- [x] Staff review interface
- [x] Secure access token generation
- [x] Email notifications
- [x] Comprehensive tests

You can now proceed to Part 5: Testing Implementation.

## Troubleshooting

### Common Issues

1. File Upload Problems
   - Check form enctype
   - Verify file size limits
   - Check upload directory permissions

2. Email Notification Issues
   - Verify email settings in settings.py
   - Check spam folder
   - Validate email templates

3. Access Token Problems
   - Check token generation
   - Verify expiration calculation
   - Validate access URL construction

### Security Considerations
- Always validate document authenticity
- Implement rate limiting for requests
- Use secure file storage
- Implement audit logging
- Regular token cleanup
- Secure email communications
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
    file = models.FileField(upload_to='probate_docs/', validators=[validate_pdf_file])
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='UPLOADED')
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
        return f'Probate Grant for {self.user.username} ({self.status})'

class VaultAccess(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    granted = models.BooleanField(default=False)
    granted_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f'Vault Access for {self.user.username} ({self.granted})'

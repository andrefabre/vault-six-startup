from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Asset, ProbateGrant

class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True)
    terms_accepted = forms.BooleanField(
        required=True,
        label='I accept the Terms of Service and Privacy Policy'
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'terms_accepted')

class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['category', 'name', 'note']
        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }

class ProbateUploadForm(forms.ModelForm):
    class Meta:
        model = ProbateGrant
        fields = ['file']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf',
            })
        }
        help_texts = {
            'file': 'Upload your probate grant document (PDF format, max 2MB)'
        }
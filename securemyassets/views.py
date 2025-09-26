from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .forms import SignUpForm, AssetForm
from .models import Asset, VaultAccess
from django.utils import timezone

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

@login_required
def dashboard(request):
    # Get user's assets
    assets = Asset.objects.filter(user=request.user).order_by('category', 'name')
    
    # Handle new asset form
    if request.method == 'POST':
        form = AssetForm(request.POST)
        if form.is_valid():
            asset = form.save(commit=False)
            asset.user = request.user
            asset.save()
            messages.success(request, 'Asset added successfully!')
            return redirect('dashboard')
    else:
        form = AssetForm()
    
    # Get vault access status
    vault_access = VaultAccess.objects.get(user=request.user)
    
    context = {
        'assets': assets,
        'form': form,
        'vault_access': vault_access,
    }
    return render(request, 'app/dashboard.html', context)

@login_required
def asset_delete(request, pk):
    asset = Asset.objects.get(pk=pk, user=request.user)
    asset.delete()
    messages.success(request, 'Asset deleted successfully!')
    return redirect('dashboard')

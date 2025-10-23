from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.http import HttpResponseForbidden
from .forms import SignUpForm, AssetForm, ProbateUploadForm
from .models import Asset, VaultAccess, ProbateGrant
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

def home(request):
    """Landing page view."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'app/home.html')

@login_required
def dashboard(request):
    # Get user's assets for the summary
    assets = Asset.objects.filter(user=request.user).order_by('category', 'name')
    
    # Get or create vault access status
    vault_access, created = VaultAccess.objects.get_or_create(
        user=request.user,
        defaults={'granted': False}
    )
    
    # Get probate status
    probate_grant = ProbateGrant.objects.filter(user=request.user).first()
    
    context = {
        'assets': assets,
        'vault_access': vault_access,
        'probate_grant': probate_grant,
    }
    return render(request, 'app/dashboard.html', context)

@login_required
def assets(request):
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
            return redirect('assets')
    else:
        form = AssetForm()
    
    context = {
        'assets': assets,
        'form': form,
    }
    return render(request, 'app/assets.html', context)

@login_required
def requests(request):
    # Get or create vault access status
    vault_access, created = VaultAccess.objects.get_or_create(
        user=request.user,
        defaults={'granted': False}
    )
    
    # Get probate status
    probate_grant = ProbateGrant.objects.filter(user=request.user).first()
    
    context = {
        'vault_access': vault_access,
        'probate_grant': probate_grant,
        'upload_form': ProbateUploadForm(),
    }
    return render(request, 'app/requests.html', context)
    return render(request, 'app/dashboard.html', context)

@login_required
def asset_delete(request, pk):
    asset = Asset.objects.get(pk=pk, user=request.user)
    asset.delete()
    messages.success(request, 'Asset deleted successfully!')
    return redirect('dashboard')

@login_required
def probate_upload(request):
    # Check if user already has a probate grant
    existing_grant = ProbateGrant.objects.filter(user=request.user).first()
    
    if request.method == 'POST':
        if existing_grant and existing_grant.status != 'REJECTED':
            messages.error(request, 'You already have a probate grant submitted.')
            return redirect('dashboard')
        
        form = ProbateUploadForm(request.POST, request.FILES)
        if form.is_valid():
            probate = form.save(commit=False)
            probate.user = request.user
            probate.status = 'UPLOADED'
            probate.save()
            messages.success(request, 'Your probate grant has been uploaded successfully and is pending review.')
            return redirect('dashboard')
    else:
        form = ProbateUploadForm()
    
    context = {
        'form': form,
        'existing_grant': existing_grant,
    }
    return render(request, 'app/probate_upload.html', context)

def staff_required(function):
    """Decorator for views that checks if the user is staff."""
    actual_decorator = user_passes_test(lambda u: u.is_staff)
    return actual_decorator(function)

@login_required
@staff_required
def review_queue(request):
    """View for staff to see pending probate grant submissions."""
    pending_grants = ProbateGrant.objects.filter(status='UPLOADED').order_by('created_at')
    context = {
        'pending_grants': pending_grants
    }
    return render(request, 'app/review_queue.html', context)

@login_required
@staff_required
def review_probate(request, pk, action):
    """Handle approval or rejection of probate grants."""
    if action not in ['approve', 'reject']:
        messages.error(request, 'Invalid action.')
        return redirect('review_queue')
        
    probate = get_object_or_404(ProbateGrant, pk=pk)
    if probate.status != 'UPLOADED':
        messages.error(request, 'This probate grant has already been reviewed.')
        return redirect('review_queue')
    
    probate.status = 'APPROVED' if action == 'approve' else 'REJECTED'
    probate.reviewed_at = timezone.now()
    probate.reviewed_by = request.user
    
    if action == 'approve':
        # Grant vault access
        vault_access = VaultAccess.objects.get(user=probate.user)
        vault_access.granted = True
        vault_access.granted_at = timezone.now()
        vault_access.save()
        messages.success(request, f'Probate grant for {probate.user.username} has been approved and vault access granted.')
    else:
        # Handle rejection
        review_notes = request.POST.get('review_notes')
        if not review_notes:
            messages.error(request, 'Please provide rejection reasons.')
            return redirect('review_queue')
        probate.review_notes = review_notes
        messages.success(request, f'Probate grant for {probate.user.username} has been rejected.')
    
    probate.save()
    return redirect('review_queue')

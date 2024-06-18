from .models import About
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.utils.decorators import method_decorator
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging
from util.security.auth_tools import is_admin_provider,is_admin_required
from .forms import AboutForm



conn = File()
# views.py
@method_decorator(login_required)
@method_decorator(is_admin_required)
def edit_about(request):
    about = About.objects.first()
    
    if request.method == 'POST':
        form = AboutForm(request.POST, request.FILES, instance=about)
        if form.is_valid():
            form.save()
            return redirect('about_view')
    else:
        form = AboutForm(instance=about)
    
    context = {
        'form': form,
        'about': about,
        'image': about.image.url if about and about.image else None,
        'primary_title': "Edit About Page"
    }
    return render(request, 'about/edit.html', context)

@method_decorator(login_required)
@method_decorator(is_admin_required)
def create_about(request):
    if request.method == 'POST':
        form = AboutForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('about_view')
    else:
        form = AboutForm()
    
    context = {
        'form': form,
        'primary_title': "Create About Page"
    }
    return render(request, 'about/create.html', context)


# Define the about view
@method_decorator(is_admin_provider)
def about(request, is_admin):
    about = About.objects.first() or default.About()
    try:
        image = conn.get_URL(about.image)
    except ParamValidationError:
        image = default.image

    if about:
        logging.info("Image S3 URL accessed:" + about.image)

    return render(request, "about.html", {
        'about': about,
        'is_admin': is_admin,
        'image': image,
        'primary_title': "About Us"
    })
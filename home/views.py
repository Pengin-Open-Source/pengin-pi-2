from .models import Home
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging
from util.security.auth_tools import is_admin_provider
from .forms import HomeForm

conn = File()

# Define the home view
@is_admin_provider
def home(request, is_admin):
    home = Home.objects.first() or default.Home()
    try:
        image = conn.get_URL(home.image)
    except ParamValidationError:
        image = default.image

    if home:
        logging.info("S3 Image accessed: " + home.image)

    return render(request, "home.html", {
        'is_admin': is_admin,
        'home': home,
        'image': image
    })
    
# views.py


@login_required
@permission_required('main.change_home', raise_exception=True)
def home_edit(request):
    home_instance = Home.objects.first()

    if request.method == 'POST':
        form = HomeForm(request.POST, request.FILES, instance=home_instance)
        if form.is_valid():
            form.save()
            return redirect('home_view')
    else:
        form = HomeForm(instance=home_instance)

    context = {
        'form': form,
        'home': home_instance,
        'image': home_instance.image if home_instance and home_instance.image else None,
        'section_title': 'Edit Home Page Info',
        'item_title': 'Edit Home Page',
        'primary_title': 'Edit Home Page',
    }
    return render(request, 'home/edit.html', context)

@login_required
@permission_required('main.add_home', raise_exception=True)
def home_create(request):
    if request.method == 'POST':
        form = HomeForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('home_view')
    else:
        form = HomeForm()

    context = {
        'form': form,
        'section_title': 'Create Home Page',
        'primary_title': 'Create Home Page',
    }
    return render(request, 'home/create.html', context)

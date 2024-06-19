from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from util.security.auth_tools import is_admin_required, is_admin_provider
from .models import About
from .forms import AboutForm
from werkzeug.utils import secure_filename
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging

conn = File()

def save_about(request, form):
    about = form.save(commit=False)
    image = request.FILES.get('image')
    
    if image:
        image.filename = secure_filename(image.name)
        about.image = conn.create(image)
        
    about.save()
    return about


@method_decorator(login_required, name='dispatch')
@method_decorator(is_admin_provider, name='dispatch')
class AboutView(View):
    def get(self, request, is_admin):
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
@method_decorator(login_required, name='dispatch')
@method_decorator(is_admin_required, name='dispatch')
class AboutEdit(View):
    def get(self, request):
        about_instance = About.objects.first()
        form = AboutForm(instance=about_instance)
        
        context = {
            'form': form,
            'about': about_instance,
            'image': conn.get_URL(about_instance.image) if about_instance and about_instance.image else None,
            'section_title': 'Edit About Page Info',
            'item_title': 'Edit About Page',
            'primary_title': 'Edit About Page',
        }
        return render(request, 'about_edit.html', context)
    
    def post(self, request):
        about_instance = About.objects.first()
        form = AboutForm(request.POST, request.FILES, instance=about_instance)
        if form.is_valid():
            about_instance = save_about(request, form)
            return redirect('about_view')  # Redirect to the correct URL

        context = {
            'form': form,
            'about': about_instance,
            'image': conn.get_URL(about_instance.image) if about_instance and about_instance.image else None,
            'section_title': 'Edit About Page Info',
            'item_title': 'Edit About Page',
            'primary_title': 'Edit About Page'
        }
        return render(request, 'about_edit.html', context)

@method_decorator(login_required, name='dispatch')
@method_decorator(is_admin_required, name='dispatch')
class AboutCreate(View):
    def get(self, request):
        form = AboutForm()
        
        context = {
            'form': form,
            'section_title': 'Create About Page',
            'primary_title': 'Create About Page'
        }
        return render(request, 'about_create.html', context)
    
    def post(self, request):
        form = AboutForm(request.POST, request.FILES)
        if form.is_valid():
            about_instance = save_about(request, form)
            return redirect('about_view')  # Redirect to the correct URL

        context = {
            'form': form,
            'section_title': 'Create About Page',
            'primary_title': 'Create About Page'
        }
        return render(request, 'about_create.html', context)

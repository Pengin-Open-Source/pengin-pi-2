from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from util.security.auth_tools import is_admin_required
from .models import Home
from .forms import HomeForm
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging

conn = File()

@method_decorator(login_required, name='dispatch')
class HomeView(View):
    def get(self, request):
        conn = File()  # Instantiate File object
        home = Home.objects.first() or default.Home()
        try:
            image = conn.get_URL(home.image)
        except ParamValidationError:
            image = default.image
        
        if home:
            logging.info("S3 Image accessed: " + home.image)
        
        return render(request, "home.html", {
            'is_admin': request.user.is_authenticated and request.user.is_staff,
            'home': home,
            'image': image,
        })


@method_decorator(login_required, name='dispatch')
@method_decorator(is_admin_required, name='dispatch')
class HomeEdit(View):
    def get(self, request):
        conn = File()  # Instantiate File object
        home_instance = Home.objects.first()
        form = HomeForm(instance=home_instance)
        
        context = {
            'form': form,
            'home': home_instance,
            'image': conn.get_URL(home_instance.image) if home_instance and home_instance.image else None,
            'section_title': 'Edit Home Page Info',
            'item_title': 'Edit Home Page',
            'primary_title': 'Edit Home Page',
        }
        return render(request, 'edit.html', context)
    
    def post(self, request):
        conn = File()  # Instantiate File object
        home_instance = Home.objects.first()
        form = HomeForm(request.POST, request.FILES, instance=home_instance)
        if form.is_valid():
            # Upload file to S3 if it exists in request.FILES
            if 'image' in request.FILES:
                home_instance.image = conn.create(request.FILES['image'])
            form.save()
            return redirect('home_view')

        context = {
            'form': form,
            'home': home_instance,
            'image': conn.get_URL(home_instance.image) if home_instance and home_instance.image else None,
            'section_title': 'Edit Home Page Info',
            'item_title': 'Edit Home Page',
            'primary_title': 'Edit Home Page',
        }
        return render(request, 'edit.html', context)


@method_decorator(login_required, name='dispatch')
@method_decorator(is_admin_required, name='dispatch')
class HomeCreate(View):
    def get(self, request):
        conn = File()  # Instantiate File object
        form = HomeForm()

        context = {
            'form': form,
            'section_title': 'Create Home Page',
            'primary_title': 'Create Home Page',
        }
        return render(request, 'create.html', context)
    
    def post(self, request):
        conn = File()  # Instantiate File object
        form = HomeForm(request.POST, request.FILES)
        if form.is_valid():
            home_instance = form.save(commit=False)
            home_instance.image = conn.create(request.FILES['image'])
            home_instance.save()
            return redirect('home_view')

        context = {
            'form': form,
            'section_title': 'Create Home Page',
            'primary_title': 'Create Home Page',
        }
        return render(request, 'create.html', context)

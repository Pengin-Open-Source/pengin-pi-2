from .models import About
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging


conn = File()

# Define the about view
def about(request):
    about = About.objects.first() or default.About()
    is_admin = request.user.is_authenticated and request.user.is_staff
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
from .models import About
from django.shortcuts import render
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging
from util.security.auth_tools import is_admin_provider


conn = File()

# Define the about view
@is_admin_provider
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
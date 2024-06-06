from .models import Home
from django.shortcuts import render
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging
from util.security.auth_tools import is_admin_provider


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
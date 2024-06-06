from .models import Home
from django.shortcuts import render
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging


conn = File()

# Define the home view
def home(request):
    home = Home.objects.first() or default.Home()
    is_admin = request.user.is_authenticated and request.user.is_staff
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
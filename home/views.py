from .models import Home
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from util.s3 import File
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging


conn = File()

# Define the home view
def home(request):
    home = Home.objects.first() or default.Home()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
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
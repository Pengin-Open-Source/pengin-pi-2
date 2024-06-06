from models import About
from django.shortcuts import render
from django.contrib.auth.decorators import user_passes_test
from util.s3 import conn
from botocore.exceptions import ParamValidationError
from util.defaults import default
import logging


# Define the about view
def about(request):
    about = About.objects.first() or default.About()
    is_admin = user_passes_test(lambda u: u.is_staff)(request.user)
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
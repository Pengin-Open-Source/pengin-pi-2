import os
import requests
from functools import wraps
from django.http import JsonResponse
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()

VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
SECRET_KEY = os.getenv("SECRET_KEY")

def verify_response(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.method == 'POST':
            response = request.POST.get('g-recaptcha-response')
            g_response = requests.post(url=f'{VERIFY_URL}?secret={SECRET_KEY}&response={response}').json()
            if not g_response["success"] or g_response["score"] < 0.6:
                return JsonResponse({"error": "human verification failed"}, status=403)
        return view_func(request, *args, **kwargs)
    return _wrapped_view

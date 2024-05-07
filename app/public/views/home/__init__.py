from django.http import HttpResponse
from django.shortcuts import render

# Define the home view
def home(request):
    return render(request, 'home.html')

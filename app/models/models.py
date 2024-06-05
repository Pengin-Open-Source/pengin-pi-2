"""
Relationships file
Add all cross application relationships in this file    
"""
from django.db import models

# Import all your models here
from models.blog import BlogPost
# Causes a conflict with the builtin in User model,  unless we set AUTH_USER_MODEL setting in settings.py
from models.customer import User, UserRoles, Role, Company, CompanyMembers
from models.public import Home, About


# Define relationships between models

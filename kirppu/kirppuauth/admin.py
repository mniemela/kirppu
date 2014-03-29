from django.contrib.auth.admin import UserAdmin
from kirppu.kirppuauth.models import User
from django.contrib import admin

__author__ = 'codez'

admin.site.register(User, UserAdmin)

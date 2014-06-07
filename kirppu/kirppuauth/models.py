from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(max_length=64, blank=False, null=False)
    last_checked = models.DateTimeField(auto_now_add=True)

    def is_vendor(self, event=None):
        return self.vendor_set.exists()

    def is_clerk(self, event=None):
        return self.clerk_set.exists()

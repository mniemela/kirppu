from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone = models.CharField(max_length=64, blank=False, null=False)
    last_checked = models.DateTimeField(auto_now_add=True)

    def is_clerk(self):
        return hasattr(self, 'clerk')

    @property
    def print_name(self):
        name = u"{0} {1}.".format(self.first_name, self.last_name[:1]).strip()
        if len(name) == 0:
            return self.username
        return name.title()

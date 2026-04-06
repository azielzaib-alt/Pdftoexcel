from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_lifetime_free = models.BooleanField(default=False)
    conversions_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "Lifetime" if self.is_lifetime_free else "Standard"
        return f"{self.user.username} - {status}"

    @property
    def can_convert(self):
        if self.is_lifetime_free:
            return True
        return self.conversions_used < 5

from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    plan = models.CharField(max_length=20, default='free', choices=[
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ])
    conversions_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.plan}"

    @property
    def conversions_limit(self):
        limits = {'free': 5, 'pro': 100, 'enterprise': 99999}
        return limits.get(self.plan, 5)

    @property
    def can_convert(self):
        return self.conversions_used < self.conversions_limit

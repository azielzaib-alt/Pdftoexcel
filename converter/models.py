from django.db import models
from django.contrib.auth.models import User


class Conversion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversions')
    filename = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('done', 'Done'),
        ('failed', 'Failed'),
    ])
    rows_extracted = models.IntegerField(default=0)
    reasoning = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.filename}"

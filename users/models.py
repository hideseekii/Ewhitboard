# users/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField("大頭貼", upload_to='avatars/', blank=True, null=True)
    bio = models.TextField("個人簡介", blank=True)
    is_registered = models.BooleanField("已完成註冊", default=False)

    def __str__(self):
        return f"{self.user.username} 的個人檔案"

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    instance.profile.save()
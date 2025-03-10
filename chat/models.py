from django.db import models
from django.contrib.auth.models import User
import uuid

from django.dispatch import receiver
from django.db.models.signals import post_save

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Contact(models.Model):
    user = models.ForeignKey(User, related_name='contacts', on_delete=models.CASCADE)
    contact = models.ForeignKey(User, related_name='contacted_by', on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'contact')

    def __str__(self):
        return f"{self.user.username}'s contact: {self.contact.username}"

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, blank=True)
    participants = models.ManyToManyField(User, related_name='rooms')
    created_at = models.DateTimeField(auto_now_add=True)
    is_direct = models.BooleanField(default=True)  # True for direct messages, False for group chats

    def __str__(self):
        if self.name:
            return self.name
        return ", ".join([user.username for user in self.participants.all()])

class Message(models.Model):
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('audio', 'Audio'),
        ('file', 'File'),
    )
    
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"
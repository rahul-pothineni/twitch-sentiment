from django.db import models
from django.utils import timezone
import uuid

class Session(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    start_time=models.DateTimeField(default=timezone.now)
    end_time=models.DateTimeField(null=True, blank=True)


class Streamer(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name="streamers")
    username = models.CharField(max_length=25)

class Message(models.Model):
    streamer = models.ForeignKey(Streamer, on_delete=models.CASCADE, related_name="messages")
    #sender_username = models.CharField(max_length=25)
    content = models.TextField()
    sent_at = models.DateTimeField(default=timezone.now)
    sentiment = models.FloatField(null = True, blank = True)


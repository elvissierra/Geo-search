import uuid
from django.db import models
from geo_search_api.apps.topics.models import Topic
from geo_search_api.apps.ideas.models import Idea


class ContributorStatus(models.TextChoices):
    INNOVATOR = "Innovator"
    ACCELERATOR = "Accelerator"


class Contributor(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.CharField(max_length=255, blank=False, null=True)
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE)
    idea = models.ForeignKey(Idea, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=255, choices=ContributorStatus.choices, blank=True, null=True
    )
    prize = models.CharField(max_length=255, blank=True, null=True)

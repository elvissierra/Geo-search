import uuid
from django.db import models
from django.contrib.contenttypes import fields as ct_fields
from django.contrib.postgres.fields import ArrayField

from geo_search_api.apps.topics.models import Topic

from geo_search_api.apps.comments.models import Comment, CommentsModelMixin
from geo_search_api.apps.likes.models import Like, LikeModelMixin


class IdeaStatuses(models.TextChoices):
    UNDER_REVIEW = "Under review"
    REJECTED = "Rejected"
    ACTIVE = "Active"
    CLOSED = "Closed"
    INNOVATIVE = "Innovative"


class Idea(models.Model, CommentsModelMixin, LikeModelMixin):
    class Meta:
        ordering = ["-is_trending", "-created_at"]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    topic = models.ForeignKey(Topic, related_name="ideas", on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=False, null=False)
    description = models.TextField()
    owner = models.CharField(max_length=255, blank=False, null=False)
    status = models.CharField(
        max_length=255, choices=IdeaStatuses.choices, null=False, default=IdeaStatuses.UNDER_REVIEW
    )
    likes = ct_fields.GenericRelation(
        to=Like, object_id_field="object_id", content_type_field="object_type"
    )
    attachments = ArrayField(
        base_field=models.CharField(max_length=200, null=True), default=list, blank=True
    )
    is_trending = models.BooleanField(default=False)
    engagement_rate = models.FloatField(blank=True, null=True)
    comments = ct_fields.GenericRelation(
        to=Comment, object_id_field="object_id", content_type_field="object_type"
    )

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now_add=True, editable=False)

    def create_contributor(self, user_id):
        """
        Creates a contributor instance with associated idea and topic.
        """
        from geo_search_api.apps.contributors.models import Contributor  # pylint: disable=C0415

        Contributor.objects.create(user=user_id, topic=self.topic, idea=self)

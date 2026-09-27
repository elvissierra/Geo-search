import uuid
from django.db import models
from django.contrib.contenttypes import fields as ct_fields

from geo_search_api.apps.likes.models import LikeModelMixin, Like
from geo_search_api.apps.comments.models import Comment, CommentsModelMixin


class NoteTypes(models.TextChoices):
    POST = "Post"
    IDEA = "Idea"


class Note(models.Model, LikeModelMixin, CommentsModelMixin):
    class Meta:
        ordering = ["-created_at"]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    category = models.CharField(max_length=255, choices=NoteTypes.choices, blank=False, null=False)
    owner = models.CharField(max_length=255, blank=False, null=False)
    content = models.TextField()
    likes = ct_fields.GenericRelation(
        to=Like, object_id_field="object_id", content_type_field="object_type"
    )
    comments = ct_fields.GenericRelation(
        to=Comment, object_id_field="object_id", content_type_field="object_type"
    )
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=False)

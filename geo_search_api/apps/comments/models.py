import uuid
from django.db import models as db_models
from django.contrib.contenttypes import fields as ct_fields
from django.contrib.contenttypes import models as ct_models
from geo_search_api.apps.likes.models import Like, LikeModelMixin


class CommentsModelMixin:  # pylint: disable=R0903
    @property
    def comments_count(self) -> int:
        """
        The total number of comments
        """
        return self.comments.count()


class Comment(db_models.Model, LikeModelMixin):
    class Meta:
        ordering = ["created_at"]
        indexes = [
            db_models.Index(fields=["object_type", "object_id"], name="comment_index_type_id"),
        ]

    id = db_models.UUIDField(default=uuid.uuid4, primary_key=True)

    # See https://docs.djangoproject.com/en/4.1/ref/contrib/contenttypes/#generic-relations
    liked_object = ct_fields.GenericForeignKey("object_type", "object_id")
    object_type = db_models.ForeignKey(ct_models.ContentType, on_delete=db_models.CASCADE)
    object_id = db_models.UUIDField()

    parent_id = db_models.ForeignKey(
        "self", related_name="replies", on_delete=db_models.CASCADE, null=True, blank=True
    )
    owner = db_models.CharField(max_length=255, blank=False, null=False)
    content = db_models.TextField()
    likes = ct_fields.GenericRelation(
        to=Like, object_id_field="object_id", content_type_field="object_type"
    )
    created_at = db_models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = db_models.DateTimeField(auto_now_add=True, editable=False)

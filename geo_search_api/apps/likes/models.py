import uuid
import collections
from django.db import models as db_models
from django.contrib.contenttypes import fields as ct_fields
from django.contrib.contenttypes import models as ct_models


LikesSumUp = collections.namedtuple(
    "LikesSumUp",
    (
        "count",
        "is_current_user_liked",
        "results",
    ),
)


class LikeModelMixin:
    @property
    def likes_count(self) -> int:
        """
        The total number of likes
        """
        return self.likes.count()

    def does_the_user_liked(self, user_id) -> bool:
        """
        Checks if the user liked the object
        """
        return self.likes.filter(user_id=user_id).exists()

    def get_likes_sum_up(self, user_id: str) -> LikesSumUp:
        """
        The usm up of likes
        """
        number_of_likes = self.likes_count
        return LikesSumUp(
            number_of_likes,
            self.does_the_user_liked(user_id),
            [self.likes.first()] if number_of_likes else [],
        )


class Like(db_models.Model):
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            db_models.Index(fields=["object_type", "object_id"], name="like_index_type_id"),
        ]
        constraints = [
            db_models.UniqueConstraint(
                fields=["object_type", "object_id", "user_id"],
                name="like_unique_type_id_user",
            )
        ]

    id = db_models.UUIDField(default=uuid.uuid4, primary_key=True)

    # See https://docs.djangoproject.com/en/4.1/ref/contrib/contenttypes/#generic-relations
    liked_object = ct_fields.GenericForeignKey("object_type", "object_id")
    object_type = db_models.ForeignKey(ct_models.ContentType, on_delete=db_models.CASCADE)
    object_id = db_models.UUIDField()

    user_id = db_models.CharField(max_length=255, blank=False, null=False)
    created_at = db_models.DateTimeField(auto_now_add=True, editable=False)

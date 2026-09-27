import uuid
from django.db import models
from django.apps import apps


class TopicTypes(models.TextChoices):
    EXPERIMENTATION = "Experimentation"
    MOONSHOT = "Moonshot"


class Topic(models.Model):
    class Meta:
        ordering = ["-created_at"]

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    owner = models.CharField(max_length=255, blank=False, null=False)

    topic_type = models.CharField(
        max_length=255, choices=TopicTypes.choices, blank=False, null=False
    )
    stage = models.ForeignKey("TopicStage", on_delete=models.DO_NOTHING, blank=False, null=False)
    title = models.CharField(max_length=255, blank=False, null=False)
    prize = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tags = models.ManyToManyField("TopicTag", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    updated_at = models.DateTimeField(auto_now=True, editable=True)

    def __str__(self):
        return f"Title: {self.title} | Prize: {self.prize} | Stage: {self.stage}"

    @property
    def contributors_count(self) -> int:
        """
        Total amount of users who posted ideas for this topic + total amount of users who
        commented the ideas within topic (w/o duplicates).
        """
        # Use defer import to avoid the error with circular import.
        from geo_search_api.apps.ideas.models import IdeaStatuses  # pylint: disable=C0415

        idea_ids = self.ideas.filter(status=IdeaStatuses.ACTIVE).values_list("id", flat=True)

        users_who_posted_ideas = list(
            apps.get_model("ideas", "Idea")
            .objects.filter(id__in=idea_ids)
            .values_list("owner", flat=True)
            .order_by("owner")
            .distinct("owner")
        )
        users_who_commented_ideas = list(
            apps.get_model("comments", "Comment")
            .objects.filter(object_id__in=idea_ids)
            .values_list("owner", flat=True)
            .order_by("owner")
            .distinct("owner")
        )

        return len(set(users_who_posted_ideas + users_who_commented_ideas))

    def ideas_count(self) -> int:
        """
        Total amount of ideas
        """
        # Use defer import to avoid the error with circular import.
        from geo_search_api.apps.ideas.models import IdeaStatuses  # pylint: disable=C0415

        return self.ideas.filter(status=IdeaStatuses.ACTIVE).count()

    @property
    def stage_name(self) -> str:
        """
        The stage name of the topic
        """
        return self.stage.name


class TopicStage(models.Model):
    class Meta:
        ordering = ["name"]
        db_table = "topic_stage"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class TopicTag(models.Model):
    class Meta:
        ordering = ["name"]
        db_table = "topic_tag"

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

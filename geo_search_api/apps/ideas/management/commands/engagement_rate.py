from datetime import timedelta, datetime, timezone
from django.core.management.base import BaseCommand
from geo_search_api.apps.ideas.models import Idea
from geo_search_api.apps.topics.models import Topic


class Command(BaseCommand):
    """
    Calculate the engagement rate command
    """

    help = "Calculate the engagement rate for ideas."

    def __init__(self, stdout=None, stderr=None, no_color=False, force_color=False):
        super().__init__(stdout, stderr, no_color, force_color)
        self._days_ago = 3
        self._comments_multiplier = 0.6
        self._users_multiplier = 0.3
        self._likes_multiplier = 0.1

    def add_arguments(self, parser):
        """
        Add the command options
        """
        parser.add_argument(
            "action",
            type=str,
            help="Set the action of the engagement rate. Available values: calculate, reset",
        )
        parser.add_argument(
            "--days-ago",
            type=int,
            action="store",
            default=3,
            help=(
                "Define the number of days for which it needs to get data for calculation. "
                "Default: 3"
            ),
        )
        parser.add_argument(
            "--comments-multiplier",
            type=int,
            action="store",
            default=0.6,
            help="Define the comments multiplier. Default: 0.6",
        )
        parser.add_argument(
            "--users-multiplier",
            type=int,
            action="store",
            default=0.3,
            help="Define the users multiplier. Default: 0.3",
        )
        parser.add_argument(
            "--likes-multiplier",
            type=int,
            action="store",
            default=0.1,
            help="Define the likes multiplier. Default: 0.1",
        )

    def handle(self, *args, **options):
        """
        Command handler
        """

        self._days_ago = int(options.get("days_ago", 3))
        self._comments_multiplier = float(options.get("comments_multiplier", 0.6))
        self._users_multiplier = float(options.get("users_multiplier", 0.3))
        self._likes_multiplier = float(options.get("likes_multiplier", 0.1))

        try:
            getattr(self, options["action"])()
        except AttributeError:
            self._write_error("Wrong action value. Available values: calculate, reset")

    def calculate(self):
        """
        Calculate the engagement rate and the trending ideas
        """

        self.stdout.write("CALCULATE:")

        self.calculate_engagement_rate()
        self.calculate_trending_ideas()

    def calculate_engagement_rate(self):
        """
        Calculate the engagement rate
        """

        self.stdout.write(" > Calculate the engagement rate for ideas:")
        start, end = self.get_last_days(days=self._days_ago)
        self.stdout.write(f"   Start date: {start.isoformat()}")
        self.stdout.write(f"   End date: {end.isoformat()}")

        for idea in Idea.objects.all():

            likes, users_who_liked = self.count_likes_and_users(idea)
            comments, users_who_commented = self.count_comments_and_users(idea)
            users_without_duplicates = set(list(users_who_liked) + list(users_who_commented))

            idea.engagement_rate = round(
                self._comments_multiplier * comments
                + self._users_multiplier * len(users_without_duplicates)
                + self._likes_multiplier * likes,
                2,
            )
            idea.save()

        self._write_success()

    def calculate_trending_ideas(self):
        """
        Set the flag `is_trending`
        """

        # Before creating a new rating table, one need to reset the previous one
        self.reset_trending_ideas()
        self.stdout.write(" > Mark the ideas as `trending idea`:")

        for topic in Topic.objects.all():
            # Mark as the trending only ideas with the engagement rate greater than 0
            query = topic.ideas.filter(engagement_rate__gt=0.0).order_by("-engagement_rate")

            ideas = query.count()
            if not ideas:
                continue

            number_of_trending = 2
            if 1 <= ideas <= 5:
                number_of_trending = 1
            elif ideas > 10:
                number_of_trending = 3

            update_query = Idea.objects.filter(
                id__in=list(query.values_list("id", flat=True)[:number_of_trending])
            )
            update_query.update(is_trending=True)
            self.stdout.write(
                f"   For topic `{topic.title}` marked {update_query.count()} idea(s) as trending"
            )

        self._write_success()

    def reset(self):
        """
        Reset all calculations related to engagement rate
        """

        self.stdout.write("RESET:")

        self.reset_engagement_rate()
        self.reset_trending_ideas()

    def reset_engagement_rate(self):
        """
        Reset the engagement rate
        """
        self.stdout.write(" > Reset the engagement rate for ideas:")
        Idea.objects.update(engagement_rate=None)
        self._write_success()

    def reset_trending_ideas(self):
        """
        Reset the flag `is_trending`
        """
        self.stdout.write(" > Reset the flag of `trending idea`:")
        Idea.objects.update(is_trending=False)
        self._write_success()

    def count_likes_and_users(self, idea: Idea):
        """
        Count the number of likes, get the list of users.
        """
        query = idea.likes.filter(**self.get_last_days(self._days_ago, True))
        return query.count(), query.values_list("user_id", flat=True)

    def count_comments_and_users(self, idea: Idea):
        """
        Count the number of comments and replies, get the list of users.
        """
        query = idea.comments.filter(**self.get_last_days(self._days_ago, True))
        return query.count(), query.values_list("owner", flat=True)

    @staticmethod
    def get_last_days(days: int, return_created_at_filter: bool = False):
        """
        Create a period of time for specific days
        """

        # Get the current time but set time at the beginning of the day
        now = datetime.now(tz=timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        if return_created_at_filter:
            return {"created_at__gte": now - timedelta(days=days), "created_at__lt": now}
        return now - timedelta(days=days), now

    def _write_success(self, message: str = "   SUCCESS"):
        """
        Write the message with `success` style
        """
        self.stdout.write(self.style.SUCCESS(message))

    def _write_error(self, message: str):
        """
        Write the message with `error` style
        """
        self.stdout.write(self.style.ERROR(message))

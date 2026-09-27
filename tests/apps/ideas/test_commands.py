import pytest
import argparse
import datetime
from geo_search_api.apps.ideas.management.commands import engagement_rate
from geo_search_api.apps.ideas.models import Idea
from geo_search_api.apps.topics.models import Topic


@pytest.fixture
def command():
    return engagement_rate.Command()


@pytest.mark.django_db
class TestCalculateEngagementRate:
    def test_add_arguments_action_positive_scenario(self, command, mocker):

        parser = argparse.ArgumentParser()

        mocked_parser_add_argument = mocker.patch.object(parser, "add_argument")

        command.add_arguments(parser)
        mocked_parser_add_argument.assert_has_calls(
            [
                mocker.call(
                    "action",
                    type=str,
                    help="Set the action of the engagement rate. Available values: calculate, reset",
                )
            ]
        )

    def test_add_arguments_days_ago_positive_scenario(self, command, mocker):

        parser = argparse.ArgumentParser()

        mocked_parser_add_argument = mocker.patch.object(parser, "add_argument")

        command.add_arguments(parser)
        mocked_parser_add_argument.assert_has_calls(
            [
                mocker.call(
                    "--days-ago",
                    type=int,
                    action="store",
                    default=3,
                    help=(
                        "Define the number of days for which it needs to get data for calculation. "
                        "Default: 3"
                    ),
                )
            ]
        )

    def test_add_arguments_comments_multiplier_positive_scenario(self, command, mocker):

        parser = argparse.ArgumentParser()

        mocked_parser_add_argument = mocker.patch.object(parser, "add_argument")

        command.add_arguments(parser)
        mocked_parser_add_argument.assert_has_calls(
            [
                mocker.call(
                    "--comments-multiplier",
                    type=int,
                    action="store",
                    default=0.6,
                    help="Define the comments multiplier. Default: 0.6",
                )
            ]
        )

    def test_add_arguments_users_multiplier_positive_scenario(self, command, mocker):

        parser = argparse.ArgumentParser()

        mocked_parser_add_argument = mocker.patch.object(parser, "add_argument")

        command.add_arguments(parser)
        mocked_parser_add_argument.assert_has_calls(
            [
                mocker.call(
                    "--users-multiplier",
                    type=int,
                    action="store",
                    default=0.3,
                    help="Define the users multiplier. Default: 0.3",
                )
            ]
        )

    def test_add_arguments_likes_multiplier_positive_scenario(self, command, mocker):

        parser = argparse.ArgumentParser()

        mocked_parser_add_argument = mocker.patch.object(parser, "add_argument")

        command.add_arguments(parser)
        mocked_parser_add_argument.assert_has_calls(
            [
                mocker.call(
                    "--likes-multiplier",
                    type=int,
                    action="store",
                    default=0.1,
                    help="Define the likes multiplier. Default: 0.1",
                )
            ]
        )

    def test_handle_option_action_negative_scenario(self, command, mocker):

        mocked_calculate = mocker.patch.object(command, "calculate")
        mocked_reset = mocker.patch.object(command, "reset")
        mocked_command_write_error = mocker.patch.object(command, "_write_error")

        command.handle(action="fake")

        mocked_calculate.assert_not_called()
        mocked_reset.assert_not_called()
        mocked_command_write_error.assert_called_once_with(
            "Wrong action value. Available values: calculate, reset"
        )

    def test_handle_option_action_calculate_positive_scenario(self, command, mocker):

        mocked_calculate = mocker.patch.object(command, "calculate")
        mocked_reset = mocker.patch.object(command, "reset")

        command.handle(action="calculate")

        mocked_calculate.assert_called_once()
        mocked_reset.assert_not_called()

    def test_handle_option_action_reset_positive_scenario(self, command, mocker):

        mocked_calculate = mocker.patch.object(command, "calculate")
        mocked_reset = mocker.patch.object(command, "reset")

        command.handle(action="reset")

        mocked_calculate.assert_not_called()
        mocked_reset.assert_called_once()

    def test_handle_option_days_ago_default_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="calculate")
        assert command._days_ago == 3

    def test_handle_option_days_ago_custom_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="calculate", days_ago=5)
        assert command._days_ago == 5

    def test_handle_option_comments_multiplier_default_value_positive_scenario(
        self, command, mocker
    ):
        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="reset")
        assert command._comments_multiplier == 0.6

    def test_handle_option_comments_multiplier_custom_value_positive_scenario(
        self, command, mocker
    ):
        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="reset", comments_multiplier=1.6)
        assert command._comments_multiplier == 1.6

    def test_handle_option_users_multiplier_default_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="calculate")
        assert command._users_multiplier == 0.3

    def test_handle_option_users_multiplier_custom_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="calculate", users_multiplier=1.3)
        assert command._users_multiplier == 1.3

    def test_handle_option_likes_multiplier_default_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="reset")
        assert command._likes_multiplier == 0.1

    def test_handle_option_likes_multiplier_custom_value_positive_scenario(self, command, mocker):

        mocker.patch.object(command, "calculate")
        mocker.patch.object(command, "reset")

        command.handle(action="reset", likes_multiplier=1.1)
        assert command._likes_multiplier == 1.1

    def test_calculate_positive_scenario(self, command, mocker):

        mocked_calculate_engagement_rate = mocker.patch.object(command, "calculate_engagement_rate")
        mocked_calculate_trending_ideas = mocker.patch.object(command, "calculate_trending_ideas")

        command.calculate()

        mocked_calculate_engagement_rate.assert_called_once()
        mocked_calculate_trending_ideas.assert_called_once()

    def test_calculate_engagement_rate_get_last_days_positive_scenario(self, command, mocker):

        mocker.patch.object(Idea.objects, "all", return_value=[])
        mocked_get_last_days = mocker.patch.object(
            command,
            "get_last_days",
            return_value=(
                datetime.datetime.now(tz=datetime.timezone.utc),
                datetime.datetime.now(tz=datetime.timezone.utc),
            ),
        )

        command.calculate_engagement_rate()

        mocked_get_last_days.assert_called_once_with(days=command._days_ago)

    def test_calculate_engagement_rate_count_likes_and_users_positive_scenario(
        self, command, mocker, prepare_ideas
    ):
        mocker.patch.object(Idea.objects, "all", return_value=prepare_ideas.ideas)
        mocker.patch.object(command, "count_comments_and_users", return_value=(1, {1, 2}))
        mocked_count_likes_and_users = mocker.patch.object(
            command, "count_likes_and_users", return_value=(1, {1, 2})
        )
        calls = [mocker.call(idea) for idea in prepare_ideas.ideas]

        command.calculate_engagement_rate()

        assert mocked_count_likes_and_users.call_count == len(prepare_ideas.ideas)
        mocked_count_likes_and_users.assert_has_calls(calls)

    def test_calculate_engagement_rate_count_comments_and_users_positive_scenario(
        self, command, mocker, prepare_ideas
    ):
        mocker.patch.object(Idea.objects, "all", return_value=prepare_ideas.ideas)
        mocker.patch.object(command, "count_likes_and_users", return_value=(1, {1, 2}))
        mocked_count_comments_and_users = mocker.patch.object(
            command, "count_comments_and_users", return_value=(1, {1, 2})
        )
        calls = [mocker.call(idea) for idea in prepare_ideas.ideas]

        command.calculate_engagement_rate()

        assert mocked_count_comments_and_users.call_count == len(prepare_ideas.ideas)
        mocked_count_comments_and_users.assert_has_calls(calls)

    def test_calculate_engagement_rate_round_positive_scenario(
        self, command, mocker, prepare_ideas
    ):
        mocker.patch.object(Idea.objects, "all", return_value=prepare_ideas.ideas)
        mocker.patch.object(command, "count_likes_and_users", return_value=(1, {1, 2}))
        mocker.patch.object(command, "count_comments_and_users", return_value=(1, {1, 2}))
        mocked_round = mocker.patch("builtins.round", return_value=1.1)

        calls = []
        for _ in prepare_ideas.ideas:
            calls.append(
                mocker.call(
                    command._comments_multiplier * 1
                    + command._users_multiplier * 2
                    + command._likes_multiplier * 1,
                    2,
                )
            )

        command.calculate_engagement_rate()

        assert mocked_round.call_count == len(prepare_ideas.ideas)
        mocked_round.assert_has_calls(calls)

    def test_calculate_engagement_rate_save_positive_scenario(self, command, mocker, prepare_ideas):
        mocker.patch.object(Idea.objects, "all", return_value=prepare_ideas.ideas)
        mocker.patch.object(command, "count_likes_and_users", return_value=(1, {1, 2}))
        mocker.patch.object(command, "count_comments_and_users", return_value=(1, {1, 2}))
        mocked_save = mocker.patch.object(Idea, "save")

        command.calculate_engagement_rate()

        assert mocked_save.call_count == len(prepare_ideas.ideas)

    def test_calculate_trending_ideas_reset_trending_ideas_positive_scenario(
        self, command, mocker, prepare_ideas
    ):

        mocker.patch.object(Topic.objects, "all", return_value=[])
        mocked_reset_trending_ideas = mocker.patch.object(command, "reset_trending_ideas")

        command.calculate_trending_ideas()

        mocked_reset_trending_ideas.assert_called_once()

    def test_calculate_trending_ideas_lt_5_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        topic = prepare_engagement_rate.topics[0]
        assert topic.ideas.count() <= 5

        mocked_filter = mocker.patch.object(Idea.objects, "filter")
        ideas = topic.ideas.order_by("-engagement_rate").all()

        command.calculate_trending_ideas()

        assert mocked_filter.call_count == len(prepare_engagement_rate.topics)
        mocked_filter.assert_has_calls(
            [mocker.call(id__in=list(ideas.values_list("id", flat=True)[:1]))]
        )

    def test_calculate_trending_ideas_continue_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):
        prepare_engagement_rate.topics[0].ideas.update(engagement_rate=0.0)

        mocked_filter = mocker.patch.object(Idea.objects, "filter")
        command.calculate_trending_ideas()
        assert mocked_filter.call_count == len(prepare_engagement_rate.topics) - 1

    def test_calculate_trending_ideas_gt_5_lt_10_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        topic = prepare_engagement_rate.topics[1]
        assert 6 <= topic.ideas.count() <= 10

        mocked_filter = mocker.patch.object(Idea.objects, "filter")
        ideas = topic.ideas.order_by("-engagement_rate").all()

        command.calculate_trending_ideas()

        assert mocked_filter.call_count == len(prepare_engagement_rate.topics)
        mocked_filter.assert_has_calls(
            [mocker.call(id__in=list(ideas.values_list("id", flat=True)[:2]))]
        )

    def test_calculate_trending_ideas_gt_10_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        topic = prepare_engagement_rate.topics[2]
        assert topic.ideas.count() > 10

        mocked_filter = mocker.patch.object(Idea.objects, "filter")
        ideas = topic.ideas.order_by("-engagement_rate").all()

        command.calculate_trending_ideas()

        assert mocked_filter.call_count == len(prepare_engagement_rate.topics)
        mocked_filter.assert_has_calls(
            [mocker.call(id__in=list(ideas.values_list("id", flat=True)[:3]))]
        )

    def test_calculate_trending_ideas_update_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        mocker.patch.object(command, "reset_trending_ideas")
        mocked_filter = mocker.patch.object(Idea.objects, "filter")
        calls = [mocker.call(is_trending=True) for _ in range(len(prepare_engagement_rate.topics))]
        command.calculate_trending_ideas()

        assert mocked_filter.return_value.update.call_count == len(prepare_engagement_rate.topics)
        mocked_filter.return_value.update.assert_has_calls(calls)

    def test_reset_positive_scenario(self, command, mocker):

        mocked_reset_engagement_rate = mocker.patch.object(command, "reset_engagement_rate")
        mocked_reset_trending_ideas = mocker.patch.object(command, "reset_trending_ideas")

        command.reset()

        mocked_reset_engagement_rate.assert_called_once()
        mocked_reset_trending_ideas.assert_called_once()

    def test_reset_engagement_rate_positive_scenario(self, command, mocker):

        mocked_update = mocker.patch.object(Idea.objects, "update")
        command.reset_engagement_rate()
        mocked_update.assert_called_once_with(engagement_rate=None)

    def test_reset_trending_ideas_positive_scenario(self, command, mocker):

        mocked_update = mocker.patch.object(Idea.objects, "update")
        command.reset_trending_ideas()
        mocked_update.assert_called_once_with(is_trending=False)

    def test_count_likes_and_users_get_last_days_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        idea = prepare_engagement_rate.ideas[0]

        mocked_get_last_days = mocker.patch.object(
            command,
            "get_last_days",
            return_value={
                "created_at__gte": datetime.datetime.now(tz=datetime.timezone.utc),
                "created_at__lt": datetime.datetime.now(tz=datetime.timezone.utc),
            },
        )

        command.count_likes_and_users(idea)

        mocked_get_last_days.assert_called_once_with(command._days_ago, True)

    def test_count_comments_and_users_get_last_days_positive_scenario(
        self, command, mocker, prepare_engagement_rate
    ):

        idea = prepare_engagement_rate.ideas[0]

        mocked_get_last_days = mocker.patch.object(
            command,
            "get_last_days",
            return_value={
                "created_at__gte": datetime.datetime.now(tz=datetime.timezone.utc),
                "created_at__lt": datetime.datetime.now(tz=datetime.timezone.utc),
            },
        )

        command.count_comments_and_users(idea)

        mocked_get_last_days.assert_called_once_with(command._days_ago, True)

    def test_get_last_days_return_created_at_filter_false_positive_scenario(self, command):
        value = command.get_last_days(3, False)
        assert len(value) == 2

    def test_get_last_days_return_created_at_filter_true_positive_scenario(self, command):
        value = command.get_last_days(3, True)
        assert "created_at__gte" in value
        assert "created_at__lt" in value

    def test_write_success_positive_scenario(self, command, mocker):

        mocked_stdout_write = mocker.patch.object(command.stdout, "write")
        mocked_style_success = mocker.patch.object(command.style, "SUCCESS")
        command._write_success("Just a message")

        mocked_style_success.assert_called_once_with("Just a message")
        mocked_stdout_write.assert_called_once()

    def test_write_error_positive_scenario(self, command, mocker):

        mocked_stdout_write = mocker.patch.object(command.stdout, "write")
        mocked_style_error = mocker.patch.object(command.style, "ERROR")
        command._write_error("Just an error")

        mocked_style_error.assert_called_once_with("Just an error")
        mocked_stdout_write.assert_called_once()

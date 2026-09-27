import collections
import uuid
import datetime
from unittest.mock import patch

import pytest
import faker
from rest_framework.test import APIClient
from django import test as dj_test

from clients.s3client import S3Client
from clients.opensearch import OpenSearchClient

from geo_search_api.apps.notes.models import Note
from geo_search_api.apps.topics.models import Topic, TopicTypes, TopicTag, TopicStage
from geo_search_api.apps.ideas.models import Idea, IdeaStatuses
from geo_search_api.apps.contributors.models import (
    Contributor,
    ContributorStatus,
)
from tests.test_data import (
    TEST_ORIGIN_OWNER,
    TEST_ANOTHER_OWNER,
    TEST_NOTES,
    TEST_LIKES,
)


@pytest.fixture
def set_auth_class(settings):
    settings.REST_FRAMEWORK["DEFAULT_AUTHENTICATION_CLASSES"] = [
        "geo_search_api.api.authentication.Auth0TokenAuthentication"
    ]


@pytest.fixture
def s3_client():
    with patch("clients.s3client.S3Client.__init__", return_value=None):
        client = S3Client()
        client.presigned_url_expiration_time_get_object = 5 * 60
        client.presigned_url_expiration_time_put_object = 60 * 60
        yield client


@pytest.fixture()
def test_app(set_auth_class, mocker):
    """
    Test application to send requests to API. Authentication is mocked as a simple user.
    """
    mocker.patch(
        "geo_search_api.api.authentication.Auth0TokenAuthentication.authenticate",
        return_value=({"id": TEST_ORIGIN_OWNER, "roles": []}, ""),
    )
    return APIClient()


@pytest.fixture()
def test_app_admin(set_auth_class, mocker):
    """
    Test application to send requests to API. Authentication is mocked ad an admin.
    """
    mocker.patch(
        "geo_search_api.api.authentication.Auth0TokenAuthentication.authenticate",
        return_value=({"id": "test_admin_id", "roles": ["admin"]}, ""),
    )
    return APIClient()


@pytest.fixture()
def test_app_unauthorized(set_auth_class):
    """
    Test application to send requests to API.
    """
    return APIClient()


@pytest.fixture
@pytest.mark.django_db
def prepare_notes():
    def _prepare():
        for note_data in TEST_NOTES:
            note = Note(**note_data)
            note.save()
            _notes_data_set.notes.append(note)

    NotesDataSet = collections.namedtuple("NotesDataSet", ["notes"])
    _notes_data_set = NotesDataSet([])

    _prepare()

    return _notes_data_set


@pytest.fixture()
@dj_test.override_settings(AWS_OPENSEARCH_HOST="http://opensearch.localhost:9200")
def mock_os_client_for_index_command(mocker):
    """
    Mock Responses from opensearch client, used by the command
    ./manage.py add_basin_index [-h] [-i INDEXNAME] [-f FILEPATH]
    """
    mocker.patch("clients.opensearch.OpenSearchClient.exists_index", return_value=(True))
    mocker.patch(
        "clients.opensearch.OpenSearchClient.create_index", return_value={"acknowledged": True}
    )
    mocker.patch(
        "clients.opensearch.OpenSearchClient.bulk",
        return_value=(True, {"cluster_name": "my_cluster"}),
    )

    return OpenSearchClient()


@pytest.fixture
@pytest.mark.django_db
def prepare_topics():
    def _prepare_tags():
        for _ in range(10):
            tag = TopicTag(id=str(uuid.uuid4()), name=_faker.text(max_nb_chars=25))
            tag.save()
            _topics_data_set.tags.append(tag)

    def _prepare_stages():
        for _ in range(3):
            stage = TopicStage(id=str(uuid.uuid4()), name=_faker.text(max_nb_chars=15))
            stage.save()
            _topics_data_set.stages.append(stage)

    def _prepare_topics():
        for _ in range(5):
            topic = Topic(
                id=str(uuid.uuid4()),
                owner=_faker.random_element(elements=(TEST_ORIGIN_OWNER, TEST_ANOTHER_OWNER)),
                topic_type=_faker.random_element(elements=TopicTypes),
                title=_faker.company(),
                stage=_faker.random_element(elements=_topics_data_set.stages),
            )
            topic.save()
            topic.tags.add(
                *_faker.random_choices(
                    elements=_topics_data_set.tags,
                    length=_faker.random_int(min=2, max=len(_topics_data_set.tags) - 1),
                )
            )
            _topics_data_set.topics.append(topic)

    TopicsDataSet = collections.namedtuple("TopicsDataSet", ["tags", "stages", "topics"])
    _topics_data_set = TopicsDataSet([], [], [])
    _faker = faker.Faker()

    _prepare_tags()
    _prepare_stages()
    _prepare_topics()

    return _topics_data_set


@pytest.fixture
@pytest.mark.django_db
def prepare_ideas(prepare_topics):
    def _prepare_ideas():
        all_idea_statuses = [status for status in IdeaStatuses] * 2
        for _ in range(10):
            idea = Idea(
                id=str(uuid.uuid4()),
                owner=_faker.random_element(elements=(TEST_ORIGIN_OWNER, TEST_ANOTHER_OWNER)),
                title=_faker.company(),
                status=all_idea_statuses[_],
                topic=_faker.random_element(elements=_ideas_data_set.topics),
                description=_faker.sentence(),
                attachments=[_faker.url(), _faker.url()],
                engagement_rate=_faker.pyfloat(min_value=0, max_value=100, right_digits=2),
                is_trending=_faker.boolean(),
            )
            idea.save()
            _ideas_data_set.ideas.append(idea)

    IdeasDataSet = collections.namedtuple("IdeasDataSet", ["ideas", "topics"])
    _ideas_data_set = IdeasDataSet([], prepare_topics.topics)
    _faker = faker.Faker()

    _prepare_ideas()

    return _ideas_data_set


@pytest.fixture
@pytest.mark.django_db
def prepare_contributors(prepare_topics, prepare_ideas):
    def _prepare_contributors():
        all_contributors_status = [status for status in ContributorStatus]
        cash_prize = [2000, 2500, 10000]
        selected_topic = prepare_topics.topics[0]
        for _ in range(3):
            contributor = Contributor(
                id=str(uuid.uuid4()),
                user=_faker.random_element(elements=(TEST_ANOTHER_OWNER, TEST_ORIGIN_OWNER)),
                topic=selected_topic,
                idea=_faker.random_element(elements=_contributors_data_set.ideas),
                status=_faker.random_element(elements=all_contributors_status),
                prize=_faker.random_element(elements=cash_prize),
            )
            contributor.save()
            _contributors_data_set.contributors.append(contributor)

    ContributorsDataSet = collections.namedtuple(
        "ContributorsDataSet", ["contributors", "topics", "ideas"]
    )
    _contributors_data_set = ContributorsDataSet([], prepare_topics.topics, prepare_ideas.ideas)
    _faker = faker.Faker()

    _prepare_contributors()

    return _contributors_data_set


@pytest.fixture
@pytest.mark.django_db
def prepare_comments(prepare_notes, prepare_ideas):
    def _prepare_comments(model):
        # Create comments
        first_comment = None
        for _ in range(4):
            comment = model.comments.create(
                id=str(uuid.uuid4()),
                content=_faker.sentence(),
                owner=_faker.random_element(elements=(TEST_ORIGIN_OWNER, TEST_ANOTHER_OWNER)),
            )
            _comments_data_set.comments.append(comment)
            if first_comment is None:
                first_comment = comment
        # Create replies
        for _ in range(2):
            reply = model.comments.create(
                id=str(uuid.uuid4()),
                content=_faker.sentence(),
                owner=_faker.random_element(elements=(TEST_ORIGIN_OWNER, TEST_ANOTHER_OWNER)),
                parent_id=first_comment,
            )
            _comments_data_set.replies.append(reply)

    def _for_notes():
        _prepare_comments(prepare_notes.notes[0])

    def _for_ideas():
        _prepare_comments(prepare_ideas.ideas[0])

    CommentsDataSet = collections.namedtuple(
        "CommentsDataSet", ["notes", "topics", "ideas", "comments", "replies"]
    )
    _comments_data_set = CommentsDataSet(
        prepare_notes.notes, prepare_ideas.topics, prepare_ideas.ideas, [], []
    )
    _faker = faker.Faker()

    _for_notes()
    _for_ideas()

    return _comments_data_set


@pytest.fixture
@pytest.mark.django_db
def prepare_likes(prepare_notes, prepare_comments, prepare_ideas):
    def _prepare_likes(model):
        for like_data in TEST_LIKES:
            like = model.likes.create(**like_data)
            _likes_data_set.likes.append(like)

    def _for_notes():
        _prepare_likes(prepare_notes.notes[0])

    def _for_comments():
        _prepare_likes(prepare_comments.comments[0])

    def _for_ideas():
        _prepare_likes(prepare_ideas.ideas[0])

    LikesDataSet = collections.namedtuple("LikesDataSet", ["notes", "comments", "ideas", "likes"])
    _likes_data_set = LikesDataSet(
        prepare_notes.notes, prepare_comments.comments, prepare_ideas.ideas, []
    )

    _for_notes()
    _for_comments()
    _for_ideas()

    return _likes_data_set


@pytest.fixture
@pytest.mark.django_db
def prepare_engagement_rate():
    """
    Prepare the data structure for the engagement rate tests. The structure is:

        TopicA(ideas_count=4):
            IdeaA1(likes_count<4)
            IdeaA2(likes_count<4)
            IdeaA3(likes_count<4)
            IdeaA4(likes_count=4)

        TopicB(ideas_count=8):
            IdeaB1(likes_count<4)
            IdeaB2(likes_count<4)
            IdeaB3(likes_count<4)
            IdeaB4(likes_count=4)
            IdeaB5(likes_count<4)
            IdeaB6(likes_count<4)
            IdeaB7(likes_count<4)
            IdeaB8(likes_count<4)

        TopicC(ideas_count=12):
            IdeaC1(likes_count<4)
            IdeaC2(likes_count<4)
            IdeaC3(likes_count<4)
            IdeaC4(likes_count=4)
            IdeaC5(likes_count<4)
            IdeaC6(likes_count<4)
            IdeaC7(likes_count<4)
            IdeaC8(likes_count<4)
            IdeaC9(likes_count<4)
            IdeaC10(likes_count<4)
            IdeaC11(likes_count<4)
            IdeaC12(likes_count<4)
    """

    def _prepare_user_ids():
        """
        Generate 4 user ids
        """
        for _ in range(4):
            _engagement_rate_data_set.user_ids.append(str(uuid.uuid4()))

    def _prepare_topic_stages():
        """
        Create 3 topic stages
        """
        for _ in range(3):
            topic_stage = TopicStage(
                id=str(uuid.uuid4()),
                name=_faker.sentence(),
            )
            topic_stage.save()
            _engagement_rate_data_set.topic_stages.append(topic_stage)

    def _prepare_topics():
        """
        Create 3 topics
        """
        for _ in range(3):
            topic = Topic(
                id=str(uuid.uuid4()),
                owner=_faker.random_element(elements=_engagement_rate_data_set.user_ids),
                topic_type=_faker.random_element(elements=TopicTypes),
                stage=_engagement_rate_data_set.topic_stages[_],
                title=_faker.sentence(),
            )
            topic.save()
            _engagement_rate_data_set.topics.append(topic)

    def _prepare_ideas():
        """
        Create ideas for topics:

         - for first topic create 4 ideas
         - for second topic create 8 ideas
         - for third topic create 12 ideas
        """
        number_of_ideas = 4
        for topic in _engagement_rate_data_set.topics:
            for _ in range(number_of_ideas):
                idea = Idea(
                    id=str(uuid.uuid4()),
                    owner=_faker.random_element(elements=_engagement_rate_data_set.user_ids),
                    title=_faker.company(),
                    status=_faker.random_element(elements=IdeaStatuses),
                    topic=topic,
                    description=_faker.text(255),
                    is_trending=_faker.boolean(),
                    engagement_rate=_faker.pyfloat(min_value=0, max_value=100, right_digits=2),
                )
                idea.save()
                _engagement_rate_data_set.ideas.append(idea)
            number_of_ideas += 4

    def _prepare_ideas_likes():
        """
        Create likes for ideas.
        For each 4-th idea create the maximum number of likes, for others the random number.
        """
        for topic in _engagement_rate_data_set.topics:
            for index, idea in enumerate(topic.ideas.all()):
                # By default, create a random number of likes.
                number_of_likes = len(_engagement_rate_data_set.user_ids) - 1
                if index == 3:
                    # For each 4-th idea create the like for each user.
                    number_of_likes = len(_engagement_rate_data_set.user_ids)

                for _ in range(_faker.pyint(min_value=1, max_value=number_of_likes)):
                    like = idea.likes.create(
                        user_id=_engagement_rate_data_set.user_ids[_],
                    )
                    like.created_at = datetime.datetime.now(
                        tz=datetime.timezone.utc
                    ) - datetime.timedelta(days=_)
                    like.save(update_fields=["created_at"])
                    _engagement_rate_data_set.likes.append(like)

    def _prepare_ideas_comments():
        """
        Create comments for ideas.
        For each 4-th idea create the maximum number of comments, for others the random number.
        """
        for topic in _engagement_rate_data_set.topics:
            for index, idea in enumerate(topic.ideas.all()):
                # By default, create a random number of comments.
                number_of_comment = len(_engagement_rate_data_set.user_ids) - 1
                if index == 3:
                    # For each 4-th idea create the comment of each user.
                    number_of_comment = len(_engagement_rate_data_set.user_ids)

                for _ in range(_faker.pyint(min_value=1, max_value=number_of_comment)):
                    comment = idea.comments.create(
                        owner=_engagement_rate_data_set.user_ids[_],
                        content=_faker.sentence(),
                    )
                    comment.created_at = datetime.datetime.now(
                        tz=datetime.timezone.utc
                    ) - datetime.timedelta(days=_)
                    comment.save(update_fields=["created_at"])
                    _engagement_rate_data_set.comments.append(comment)

                    if _ == 1:
                        # For each second comment create one reply.
                        reply = idea.comments.create(
                            content=_faker.sentence(),
                            owner=_engagement_rate_data_set.user_ids[_],
                            parent_id=comment,
                        )
                        reply.created_at = datetime.datetime.now(
                            tz=datetime.timezone.utc
                        ) - datetime.timedelta(days=_)
                        reply.save(update_fields=["created_at"])
                        _engagement_rate_data_set.comments.append(reply)

    EngagementRateDataSet = collections.namedtuple(
        "EngagementRateDataSet",
        ["user_ids", "topic_stages", "topics", "ideas", "likes", "comments"],
    )
    _engagement_rate_data_set = EngagementRateDataSet([], [], [], [], [], [])
    _faker = faker.Faker()

    _prepare_user_ids()
    _prepare_topic_stages()
    _prepare_topics()
    _prepare_ideas()
    _prepare_ideas_likes()
    _prepare_ideas_comments()

    return _engagement_rate_data_set

import json
import uuid
import math

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from geo_search_api.apps.ideas.models import IdeaStatuses
from geo_search_api.apps.topics.models import Topic, TopicTypes, TopicTag, TopicStage
from tests.test_data import TEST_ORIGIN_OWNER


@pytest.mark.django_db
class TestTopicsGetOrCreate:
    uri = reverse("TopicsGetOrCreate")
    new_topic_type = TopicTypes.MOONSHOT
    new_topic_title = "New title"

    def test_create_topic_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_create_topic_positive_scenario(self, prepare_topics, test_app):
        topic_tag = TopicTag.objects.first()
        new_topic = {
            "topic_type": self.new_topic_type,
            "title": self.new_topic_title,
            "tags": [str(topic_tag.id)],
            "stage": str(TopicStage.objects.first().id),
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_topic), content_type="application/json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data.get("topic_type") == self.new_topic_type
        assert response_data.get("title") == self.new_topic_title
        assert response_data.get("tags") == [{"id": str(topic_tag.id), "name": topic_tag.name}]
        assert response_data.get("stage_name") == str(TopicStage.objects.first().name)
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        assert response_data.get("contributors_count") == 0

        topic = Topic.objects.get(title=self.new_topic_title)
        assert topic.topic_type == self.new_topic_type
        assert topic.title == self.new_topic_title
        assert list(topic.tags.all()) == [TopicTag.objects.first()]
        assert topic.stage == TopicStage.objects.first()
        assert topic.owner == TEST_ORIGIN_OWNER

    def test_create_topic_fails_without_required_fields(self, prepare_topics, test_app):

        tag_id = str(prepare_topics.tags[0].id)
        stage_id = str(prepare_topics.stages[0].id)
        new_topic = {"title": self.new_topic_title, "tags": [tag_id], "stage": stage_id}
        response = test_app.post(
            self.uri, data=json.dumps(new_topic), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == {"topic_type": ["This field is required."]}

        new_topic = {"topic_type": self.new_topic_type, "tags": [tag_id], "stage": stage_id}
        response = test_app.post(
            self.uri, data=json.dumps(new_topic), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == {"title": ["This field is required."]}

        new_topic = {
            "topic_type": self.new_topic_type,
            "title": self.new_topic_title,
            "tags": [tag_id],
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_topic), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == {"stage": ["This field is required."]}

    def test_retrieve_all_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_retrieve_all_ok_positive_scenario(self, test_app, prepare_topics):

        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "next" in data
        assert "previous" in data
        assert data["count"] == len(prepare_topics.topics)
        assert data["total_pages"] == 1
        assert len(data["results"]) == len(prepare_topics.topics)

    def test_retrieve_all_pagination_negative_scenario(self, test_app, prepare_topics):

        response = test_app.get(self.uri, QUERY_STRING="page_size=-2&page=2")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_all_pagination_positive_scenario(self, test_app, prepare_topics):

        response = test_app.get(self.uri, QUERY_STRING="page_size=2&page=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == len(prepare_topics.topics)
        assert data["total_pages"] == math.ceil(len(prepare_topics.topics) / 2)
        assert len(data["results"]) == 2
        assert data["results"][0]["id"] == prepare_topics.topics[2].id
        assert data["results"][1]["id"] == prepare_topics.topics[1].id

    def test_retrieve_all_topic_type_query_positive_scenario(self, test_app, prepare_topics):
        response = test_app.get(self.uri, QUERY_STRING="topic_type=Experimentation")
        assert response.status_code == status.HTTP_200_OK

        count = Topic.objects.filter(topic_type="Experimentation").count()

        data = response.json()
        assert data["count"] == count
        assert len(data["results"]) == count

    def test_retrieve_all_topic_type_query_negative_scenario(self, test_app, prepare_topics):
        response = test_app.get(self.uri, QUERY_STRING="topic_type=WrongValue")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestTopicGetOrUpdateOrDelete:
    uri_name = "TopicGetOrUpdateOrDelete"

    def test_get_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.get(self._get_url(prepare_topics.topics[0].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_not_found_negative_scenario(self, test_app):
        response = test_app.get(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_positive_scenario(self, test_app, prepare_ideas):
        topic = prepare_ideas.topics[0]
        response = test_app.get(self._get_url(topic.id))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(topic.id)
        assert data["contributors_count"] == topic.contributors_count
        assert data["ideas_count"] == topic.ideas.filter(status=IdeaStatuses.ACTIVE).count()
        assert data["stage_name"] == topic.stage.name

    def test_get_contributors_count_positive_scenario(self, test_app, prepare_comments):

        topic = prepare_comments.topics[0]
        contributors = []
        for idea in topic.ideas.filter(status=IdeaStatuses.ACTIVE).all():
            if idea.owner not in contributors:
                contributors.append(idea.owner)
            for comment in idea.comments.all():
                if comment.owner not in contributors:
                    contributors.append(comment.owner)

        response = test_app.get(self._get_url(topic.id))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == topic.id
        assert data["contributors_count"] == len(contributors)

    def test_update_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.put(
            self._get_url(prepare_topics.topics[1].id), content_type="application/json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_update_not_found_negative_scenario(self, test_app):
        response = test_app.put(self._get_url(str(uuid.uuid4())), content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_update_bad_request_negative_scenario(self, test_app, prepare_topics):
        body = {"topic_type": "WrongValue", "created_at": "WrongValue"}
        response = test_app.put(
            self._get_url(prepare_topics.topics[1].id),
            data=json.dumps(body),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_positive_scenario(self, test_app, prepare_topics):
        topic = prepare_topics.topics[1]
        body = {
            "topic_type": TopicTypes.MOONSHOT,
            "title": "UpdatedTitle",
            "prize": "UpdatedPrize",
            "description": "UpdatedDescription",
            "stage": str(prepare_topics.stages[0].id),
            "tags": [],
        }
        response = test_app.put(
            self._get_url(topic.id), data=json.dumps(body), content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK

        topic_reloaded = Topic.objects.get(pk=topic.id)

        assert topic_reloaded.topic_type == body["topic_type"]
        assert topic_reloaded.title == body["title"]
        assert topic_reloaded.prize == body["prize"]
        assert topic_reloaded.description == body["description"]
        assert str(topic_reloaded.stage.id) == body["stage"]
        assert topic_reloaded.tags.count() == len(body["tags"])

    def test_delete_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.delete(self._get_url(prepare_topics.topics[2].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_delete_not_found_negative_scenario(self, test_app):
        response = test_app.delete(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_delete_positive_scenario(self, test_app, prepare_topics):
        topic = prepare_topics.topics[2]
        response = test_app.delete(self._get_url(topic.id))
        assert response.status_code == status.HTTP_200_OK

        assert not Topic.objects.filter(id=topic.id).exists()

    def _get_url(self, *args):
        return reverse(self.uri_name, args)


@pytest.mark.django_db
class TestTopicStageGetOrCreate:
    uri = reverse("TopicStageGetOrCreate")
    new_topic_stage = "New stage"

    def test_create_topic_stage_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_create_topic_stage_positive_scenario(self, test_app):
        new_stage = {
            "name": self.new_topic_stage,
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_stage), content_type="application/json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data.get("name") == self.new_topic_stage
        stage = TopicStage.objects.get(name=self.new_topic_stage)
        assert stage.name == self.new_topic_stage

    def test_create_topic_stage_fails_without_required_fields(self, test_app):
        new_stage = {
            "title": self.new_topic_stage,
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_stage), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == {"name": ["This field is required."]}

    def test_retrieve_all_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_retrieve_all_ok_positive_scenario(self, test_app, prepare_topics):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "next" in data
        assert "previous" in data
        assert data["count"] == len(prepare_topics.stages) + 2
        assert data["total_pages"] == 1
        assert len(data["results"]) == len(prepare_topics.stages) + 2

    def test_retrieve_all_pagination_positive_scenario(self, test_app, prepare_topics):
        stages = TopicStage.objects.all()
        response = test_app.get(self.uri, QUERY_STRING="page_size=2&page=1")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == len(prepare_topics.stages) + 2
        assert data["total_pages"] == math.ceil((len(prepare_topics.stages) + 2) / 2)
        assert len(data["results"]) == 2
        assert data["results"][0]["id"] == str(stages[0].id)
        assert data["results"][1]["id"] == str(stages[1].id)


@pytest.mark.django_db
class TestTopicStageGetOrUpdateOrDelete:
    uri_name = "TopicStageGetOrUpdateOrDelete"

    def test_get_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.get(self._get_url(prepare_topics.stages[0].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_not_found_negative_scenario(self, test_app):
        response = test_app.get(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_positive_scenario(self, test_app, prepare_topics):
        topic_stage = prepare_topics.stages[0]
        response = test_app.get(self._get_url(topic_stage.id))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(topic_stage.id)

    def test_update_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.put(
            self._get_url(prepare_topics.stages[1].id), content_type="application/json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_update_not_found_negative_scenario(self, test_app):
        response = test_app.put(self._get_url(str(uuid.uuid4())), content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_update_bad_request_negative_scenario(self, test_app, prepare_topics):
        body = {}
        response = test_app.put(
            self._get_url(prepare_topics.stages[1].id),
            data=json.dumps(body),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_positive_scenario(self, test_app, prepare_topics):
        topic_stage = prepare_topics.stages[1]
        body = {"name": "UpdatedName"}
        response = test_app.put(
            self._get_url(topic_stage.id), data=json.dumps(body), content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK

        topic_stage_reloaded = TopicStage.objects.get(pk=topic_stage.id)
        assert topic_stage_reloaded.name == body["name"]

    def test_delete_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.delete(self._get_url(prepare_topics.stages[2].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_delete_not_found_negative_scenario(self, test_app):
        response = test_app.delete(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_delete_forbidden_negative_scenario(self, test_app, prepare_topics):

        topic = prepare_topics.topics[2]
        topic_stage = prepare_topics.stages[2]
        topic.stage = topic_stage
        topic.save()

        response = test_app.delete(self._get_url(topic_stage.id))
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.json()

    def test_delete_positive_scenario(self, test_app, prepare_topics):
        topic_stage = prepare_topics.stages[2]
        for topic in topic_stage.topic_set.all():
            topic.stage = prepare_topics.stages[1]
            topic.save()

        assert topic_stage.topic_set.count() == 0
        # Only after this manipulation try to delete the stage.
        response = test_app.delete(self._get_url(topic_stage.id))
        assert response.status_code == status.HTTP_200_OK
        assert not TopicStage.objects.filter(id=topic_stage.id).exists()

    def _get_url(self, *args):
        return reverse(self.uri_name, args)


@pytest.mark.django_db
class TestTopicTagsGetOrCreate:
    uri = reverse("TopicTagsGetOrCreate")
    new_topic_tag = "New tag"

    def test_create_topic_tag_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_create_topic_tag_positive_scenario(self, test_app):
        new_tag = {
            "name": self.new_topic_tag,
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_tag), content_type="application/json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data.get("name") == self.new_topic_tag
        tag = TopicTag.objects.get(name=self.new_topic_tag)
        assert tag.name == self.new_topic_tag

    def test_create_topic_tag_fails_without_required_fields(self, test_app):
        new_tag = {
            "title": self.new_topic_tag,
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_tag), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()

        assert response_data == {"name": ["This field is required."]}

    def test_retrieve_all_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_retrieve_all_ok_positive_scenario(self, test_app, prepare_topics):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert "next" in data
        assert "previous" in data
        assert data["count"] == len(prepare_topics.tags)
        assert data["total_pages"] == 1
        assert len(data["results"]) == len(prepare_topics.tags)

    def test_retrieve_all_pagination_positive_scenario(self, test_app, prepare_topics):
        tags = TopicTag.objects.all()
        response = test_app.get(self.uri, QUERY_STRING="page_size=2&page=2")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["count"] == len(prepare_topics.tags)
        assert data["total_pages"] == math.ceil(len(prepare_topics.tags) / 2)
        assert len(data["results"]) == 2
        assert data["results"][0]["id"] == str(tags[2].id)
        assert data["results"][1]["id"] == str(tags[3].id)


@pytest.mark.django_db
class TestTopicTagGetOrUpdateOrDelete:
    uri_name = "TopicTagGetOrUpdateOrDelete"

    def test_get_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.get(self._get_url(prepare_topics.tags[1].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_not_found_negative_scenario(self, test_app):
        response = test_app.get(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_positive_scenario(self, test_app, prepare_topics):
        topic_tag = prepare_topics.tags[2]
        response = test_app.get(self._get_url(topic_tag.id))
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(topic_tag.id)

    def test_update_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.put(
            self._get_url(prepare_topics.tags[2].id), content_type="application/json"
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_update_not_found_negative_scenario(self, test_app):
        response = test_app.put(self._get_url(str(uuid.uuid4())), content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_update_bad_request_negative_scenario(self, test_app, prepare_topics):
        body = {}
        response = test_app.put(
            self._get_url(prepare_topics.tags[2].id),
            data=json.dumps(body),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_positive_scenario(self, test_app, prepare_topics):
        topic_tag = prepare_topics.tags[2]
        body = {"name": "UpdatedTitle"}
        response = test_app.put(
            self._get_url(topic_tag.id), data=json.dumps(body), content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK

        topic_tag_reloaded = TopicTag.objects.get(pk=topic_tag.id)
        assert topic_tag_reloaded.name == body["name"]

    def test_delete_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_topics):
        response = test_app_unauthorized.delete(self._get_url(prepare_topics.tags[3].id))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_delete_not_found_negative_scenario(self, test_app):
        response = test_app.delete(self._get_url(str(uuid.uuid4())))
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_delete_positive_scenario(self, test_app, prepare_topics):
        topic_tag = prepare_topics.tags[3]
        response = test_app.delete(self._get_url(topic_tag.id))
        assert response.status_code == status.HTTP_200_OK

        assert not TopicTag.objects.filter(id=topic_tag.id).exists()

    def _get_url(self, *args):
        return reverse(self.uri_name, args)

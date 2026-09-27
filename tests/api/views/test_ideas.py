import json
import math

import pytest
import uuid
from rest_framework import status
from rest_framework.reverse import reverse

from geo_search_api.apps.ideas.models import Idea, IdeaStatuses
from geo_search_api.apps.topics.models import TopicStage
from geo_search_api.apps.contributors.models import Contributor
from tests.test_data import TEST_ANOTHER_OWNER, TEST_ORIGIN_OWNER


@pytest.mark.django_db
class TestGetTopTrendingIdeas:
    uri = reverse("IdeasTrendingGet")

    def test_no_ideas(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data == {"detail": "No trending ideas at the moment."}

    def test_top_ideas_order(self, prepare_ideas, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) <= 5

        unique_topics = set(idea["topic"] for idea in response_data)
        if len(unique_topics) < 5:
            seen_topics = set()
            for idea in range(len(response_data) - 1):
                if (
                    response_data[idea]["engagement_rate"]
                    < response_data[idea + 1]["engagement_rate"]
                    and response_data[idea + 1]["topic"] in seen_topics
                ):
                    continue
                assert (
                    response_data[idea]["engagement_rate"]
                    >= response_data[idea + 1]["engagement_rate"]
                )
                seen_topics.add(response_data[idea]["topic"])
        else:
            assert len(unique_topics) == 5

    def test_top_ideas_order_if_duplicate_topic(self, prepare_ideas, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) <= 5

        seen_topics = {}
        for idea in response_data:
            if idea["topic"] in seen_topics:
                assert seen_topics[idea["topic"]]["engagement_rate"] > idea["engagement_rate"]
            else:
                seen_topics[idea["topic"]] = idea

        assert 1 <= len(seen_topics) <= 5

    def test_filtering_for_trending(self, prepare_ideas, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert len(response_data) <= 5

        for idea in response_data:
            assert idea["engagement_rate"] is not None
            assert idea["is_trending"] is True


@pytest.mark.django_db
class TestIdeasGetOrCreate:
    uri = reverse("IdeasGetOrCreateView")
    idea_title = "Test Title Here"
    idea_description = "Description Here"

    def test_get_all_ideas_unauthorized_positive_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_all_ideas_positive_scenario(self, prepare_ideas, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert "next" in response_data
        assert "previous" in response_data
        assert response_data["count"] == len(prepare_ideas.ideas)
        assert response_data["total_pages"] == 1
        assert len(response_data["results"]) == len(prepare_ideas.ideas)

    def test_get_all_ideas_with_pagination_params_positive_scenario(self, prepare_ideas, test_app):
        response = test_app.get(self.uri, QUERY_STRING="sort=-created_at&page_size=2&page=2")
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert response_data["count"] == len(prepare_ideas.ideas)
        assert response_data["total_pages"] == math.ceil(len(prepare_ideas.ideas) / 2)
        assert len(response_data["results"]) == 2
        assert response_data["results"][0]["id"] == prepare_ideas.ideas[7].id
        assert response_data["results"][1]["id"] == prepare_ideas.ideas[6].id

    def test_get_all_ideas_with_owner_query_positive_scenario(self, prepare_ideas, test_app):
        owner_id = prepare_ideas.ideas[0].owner
        response = test_app.get(self.uri, QUERY_STRING=f"owner={owner_id}")
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data["results"]) >= 1
        for idea in response_data["results"]:
            assert idea["owner"] == owner_id

    def test_get_all_ideas_with_topic_query_positive_scenario(self, prepare_ideas, test_app):
        topic_id = prepare_ideas.ideas[0].topic.id
        response = test_app.get(self.uri, QUERY_STRING=f"topic={topic_id}")
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data["results"]) >= 1
        for idea in response_data["results"]:
            assert idea["topic"] == topic_id

    def test_get_all_ideas_with_status_query_positive_scenario(self, prepare_ideas, test_app):
        idea_status = prepare_ideas.ideas[0].status
        response = test_app.get(self.uri, QUERY_STRING=f"status={idea_status}")
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data["results"]) >= 1
        for idea in response_data["results"]:
            assert idea["status"] == idea_status

    def test_get_all_ideas_with_combined_query_positive_scenario(self, prepare_ideas, test_app):
        idea_status = prepare_ideas.ideas[0].status
        topic_id = prepare_ideas.ideas[0].topic.id
        owner_id = prepare_ideas.ideas[0].owner
        response = test_app.get(
            self.uri, QUERY_STRING=f"status={idea_status}&topic={topic_id}&owner={owner_id}"
        )
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        assert len(response_data["results"]) >= 1
        for idea in response_data["results"]:
            assert idea["status"] == idea_status
            assert idea["topic"] == topic_id
            assert idea["owner"] == owner_id

    def test_get_all_ideas_with_order_query_negative_scenario(self, prepare_ideas, test_app):
        response = test_app.get(self.uri, QUERY_STRING="sort=wrong")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()
        assert "sort" in response_data

        response = test_app.get(self.uri, QUERY_STRING="sort=created_at,-wrong")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        response_data = response.json()
        assert "sort" in response_data

    def test_get_all_ideas_with_order_query_positive_scenario(self, prepare_ideas, test_app):

        ideas = Idea.objects.order_by("-engagement_rate", "is_trending").all()
        response = test_app.get(self.uri, QUERY_STRING="sort=-engagement_rate,is_trending")
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["results"][0]["id"] == str(ideas[0].id)
        assert response_data["results"][1]["id"] == str(ideas[1].id)

        ideas = Idea.objects.all()
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["results"][0]["id"] == str(ideas[0].id)
        assert response_data["results"][1]["id"] == str(ideas[1].id)

    def test_create_idea_positive_scenario(self, prepare_ideas, test_app):
        topic_id = str(prepare_ideas.topics[0].id)

        new_idea = {
            "title": self.idea_title,
            "description": self.idea_description,
            "topic": topic_id,
            "attachments": [],
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("topic") == topic_id
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        assert response_data.get("description") == self.idea_description
        assert response_data.get("title") == self.idea_title
        assert response_data.get("comments_count") == 0
        idea = Idea.objects.get(id=response_data["id"])
        assert str(idea.topic_id) == topic_id
        assert idea.title == self.idea_title
        assert idea.status == IdeaStatuses.ACTIVE
        assert idea.owner == TEST_ORIGIN_OWNER

        contributor = Contributor.objects.get(idea=idea)
        assert contributor is not None
        assert contributor.user == TEST_ORIGIN_OWNER
        assert str(contributor.topic.id) == topic_id
        assert str(contributor.idea.id) == str(idea.id)

    def test_create_idea_fails_for_evaluation_topic(self, prepare_ideas, test_app):
        topic_under_evaluation = prepare_ideas.topics[0]
        evaluation_stage, _ = TopicStage.objects.get_or_create(name="Evaluation")

        topic_under_evaluation.stage = evaluation_stage
        topic_under_evaluation.save()

        new_idea = {
            "title": self.idea_title,
            "description": self.idea_description,
            "topic": str(topic_under_evaluation.id),
            "attachments": [],
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert (
            response_data.get("detail")
            == f"This topic is {evaluation_stage.name}, action not permitted."
        )

    def test_create_idea_fails_for_closed_topic(self, prepare_ideas, test_app):
        topic_closed = prepare_ideas.topics[1]
        closed_stage, _ = TopicStage.objects.get_or_create(name="Closed")

        topic_closed.stage = closed_stage
        topic_closed.save()

        new_idea = {
            "title": self.idea_title,
            "description": self.idea_description,
            "topic": str(topic_closed.id),
            "attachments": [],
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert (
            response_data.get("detail")
            == f"This topic is {closed_stage.name}, action not permitted."
        )

    def test_create_idea_fails_without_title_field(self, prepare_topics, test_app):
        topic_id = str(prepare_topics.topics[0].id)
        new_idea = {
            "description": "Description here",
            "topic": topic_id,
            "status": "New",
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"title": ["This field is required."]}

    def test_create_idea_fails_without_topic_field(self, test_app):
        new_idea = {
            "title": "Test Title here",
            "description": "Description here",
            "status": "New",
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"topic": ["This field is required."]}

    def test_create_idea_fails_without_existing_topic(self, test_app):
        topic_id = str(uuid.uuid4())
        new_idea = {
            "title": "Test Title here",
            "description": "Description here",
            "topic": topic_id,
        }
        response = test_app.post(
            self.uri, data=json.dumps(new_idea), content_type="application/json"
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response_data == {"topic": [f'Invalid pk "{topic_id}" - object does not exist.']}


@pytest.mark.django_db
class TestIdeaGetOrUpdateOrDelete:
    api_name = "IdeaGetOrUpdateOrDelete"
    idea_title = "Test Title Here"
    idea_description = "Description Here"

    def test_get_idea_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_ideas):
        uri = reverse(self.api_name, (prepare_ideas.ideas[0].id,))
        response = test_app_unauthorized.get(uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_get_idea_not_found_negative_scenario(self, test_app):
        uri = reverse(self.api_name, (str(uuid.uuid4()),))
        response = test_app.get(uri)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_get_idea_positive_scenario(self, test_app, prepare_ideas):
        uri = reverse(self.api_name, (prepare_ideas.ideas[0].id,))
        response = test_app.get(uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == prepare_ideas.ideas[0].id

    def test_get_idea_comments_count_positive_scenario(self, test_app, prepare_comments):

        idea = prepare_comments.ideas[0]
        uri = reverse(self.api_name, (idea.id,))
        response = test_app.get(uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["comments_count"] == idea.comments_count

    def test_update_idea_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_ideas):
        uri = reverse(self.api_name, (prepare_ideas.ideas[1].id,))
        response = test_app_unauthorized.put(uri, content_type="application/json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_update_idea_not_found_negative_scenario(self, test_app):
        uri = reverse(self.api_name, (str(uuid.uuid4()),))
        response = test_app.put(uri, content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_update_idea_forbidden_negative_scenario(self, test_app, prepare_ideas):
        not_own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner == TEST_ANOTHER_OWNER]
        uri = reverse(self.api_name, (not_own_ideas[0].id,))
        response = test_app.put(uri, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.json()

    def test_update_idea_status_positive_scenario(self, test_app, prepare_ideas):
        own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner != TEST_ANOTHER_OWNER]
        another_statuses = [
            idea.status for idea in prepare_ideas.ideas if idea.status != own_ideas[0].status
        ]
        uri = reverse(self.api_name, (own_ideas[0].id,))
        body = {
            "status": another_statuses[0],
            "description": self.idea_description,
            "title": self.idea_title,
        }
        response = test_app.put(
            uri,
            data=json.dumps(body),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] != another_statuses[0]
        assert response.json()["status"] == own_ideas[0].status

    def test_update_idea_positive_scenario(self, test_app, prepare_ideas):
        own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner != TEST_ANOTHER_OWNER]
        uri = reverse(self.api_name, (own_ideas[0].id,))
        body = {
            "description": self.idea_description,
            "title": self.idea_title,
        }
        response = test_app.put(
            uri,
            data=json.dumps(body),
            content_type="application/json",
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data["description"] == self.idea_description
        assert response_data["title"] == self.idea_title

    def test_delete_idea_unauthorized_negative_scenario(self, test_app_unauthorized, prepare_ideas):
        own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner != TEST_ANOTHER_OWNER]
        uri = reverse(self.api_name, (own_ideas[0].id,))
        response = test_app_unauthorized.delete(uri, content_type="application/json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_delete_idea_not_found_negative_scenario(self, test_app):
        uri = reverse(self.api_name, (str(uuid.uuid4()),))
        response = test_app.delete(uri, content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_delete_idea_forbidden_negative_scenario(self, test_app, prepare_ideas):
        not_own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner == TEST_ANOTHER_OWNER]
        uri = reverse(self.api_name, (not_own_ideas[0].id,))
        response = test_app.delete(uri, content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in response.json()

    def test_delete_idea_positive_scenario(self, prepare_ideas, test_app):
        own_ideas = [idea for idea in prepare_ideas.ideas if idea.owner != TEST_ANOTHER_OWNER]
        uri = reverse(self.api_name, (own_ideas[1].id,))
        response = test_app.delete(uri, content_type="application/json")
        assert response.status_code == status.HTTP_200_OK

        idea = Idea.objects.filter(id=own_ideas[1].id).first()
        assert not idea


@pytest.mark.django_db
class TestIdeaPostStatus:
    api_name = "IdeaStatusUpdate"

    def test_idea_status_post_unauthorized_negative_scenario(
        self, test_app_unauthorized, prepare_ideas
    ):
        uri = reverse(self.api_name)
        response = test_app_unauthorized.post(uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_idea_status_post_not_found_negative_scenario(self, test_app):
        uri = reverse(self.api_name)
        body = {"id": str(uuid.uuid4()), "status": IdeaStatuses.CLOSED}
        response = test_app.post(uri, data=json.dumps(body), content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in response.json()

    def test_idea_status_post_positive_scenario(self, test_app, prepare_ideas):
        ideas_under_review = [
            idea for idea in prepare_ideas.ideas if idea.status == IdeaStatuses.UNDER_REVIEW
        ]
        uri = reverse(self.api_name)
        body = {"id": ideas_under_review[0].id, "status": IdeaStatuses.ACTIVE}
        response = test_app.post(uri, data=json.dumps(body), content_type="application/json")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == ideas_under_review[0].id
        assert data["status"] == IdeaStatuses.ACTIVE
        idea = Idea.objects.get(id=ideas_under_review[0].id)
        assert idea.status == IdeaStatuses.ACTIVE

    def test_idea_status_post_fails_with_wrong_status_workflow(self, test_app, prepare_ideas):
        ideas_under_review = [
            idea for idea in prepare_ideas.ideas if idea.status == IdeaStatuses.UNDER_REVIEW
        ]
        uri = reverse(self.api_name)
        body = {"id": ideas_under_review[0].id, "status": IdeaStatuses.CLOSED}
        response = test_app.post(uri, data=json.dumps(body), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data == {
            "non_field_errors": [
                "Wrong status. Current idea status must be changed only on Active, Rejected."
            ]
        }

        ideas_active = [idea for idea in prepare_ideas.ideas if idea.status == IdeaStatuses.ACTIVE]
        uri = reverse(self.api_name)
        body = {"id": ideas_active[0].id, "status": IdeaStatuses.INNOVATIVE}
        response = test_app.post(uri, data=json.dumps(body), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data == {
            "non_field_errors": [
                "Wrong status. Current idea status must be changed only on Closed."
            ]
        }

        ideas_innovate = [
            idea for idea in prepare_ideas.ideas if idea.status == IdeaStatuses.ACTIVE
        ]
        uri = reverse(self.api_name)
        body = {"id": ideas_innovate[0].id, "status": IdeaStatuses.ACTIVE}
        response = test_app.post(uri, data=json.dumps(body), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert data == {
            "non_field_errors": [
                "Wrong status. Current idea status must be changed only on Closed."
            ]
        }

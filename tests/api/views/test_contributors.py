import json

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from geo_search_api.apps.contributors.models import (
    Contributor,
    ContributorStatus,
)
from tests.test_data import TEST_ORIGIN_OWNER


@pytest.mark.django_db
class TestContributorGetOrCreate:
    api_name = "ContributorsGetOrCreate"

    def test_get_all_contributors(self, test_app, prepare_contributors):
        uri = reverse(self.api_name, (prepare_contributors.topics[0].id,))
        response = test_app.get(uri, content_type="application/json")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) == len(prepare_contributors.contributors)

    def test_get_all_contributors_prize_order(self, test_app, prepare_contributors):
        uri = reverse(self.api_name, args=[prepare_contributors.topics[0].id])
        response = test_app.get(uri, content_type="application/json")

        assert response.status_code == status.HTTP_200_OK

        contributors = response.json()
        assert len(contributors) == len(prepare_contributors.contributors)

        is_sorted = True
        for i in range(1, len(contributors)):
            if contributors[i]["prize"] < contributors[i - 1]["prize"]:
                is_sorted = False
                break

        assert is_sorted

    def test_create_contributor_positive_scenario(self, prepare_contributors, test_app):
        topic_id = prepare_contributors.topics[0].id
        idea_id = prepare_contributors.ideas[0].id
        new_contributor = {
            "user": TEST_ORIGIN_OWNER,
            "topic": topic_id,
            "idea": idea_id,
            "status": ContributorStatus.INNOVATOR.value,
        }

        uri = reverse(self.api_name, (prepare_contributors.topics[0].id,))
        response = test_app.post(
            uri, data=json.dumps(new_contributor), content_type="application/json"
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("user") == TEST_ORIGIN_OWNER
        assert response_data.get("topic") == topic_id
        assert response_data.get("idea") == idea_id
        assert response_data.get("status") == new_contributor["status"]

        contributor = Contributor.objects.get(id=response_data["id"])
        assert contributor.user == new_contributor["user"]
        assert str(contributor.topic.id) == new_contributor["topic"]
        assert str(contributor.idea.id) == new_contributor["idea"]
        assert contributor.status == new_contributor["status"]

    def test_negative_create_contributor_no_topic(self, prepare_contributors, test_app):
        idea = prepare_contributors.ideas[0].id
        new_contributor = {
            "user": TEST_ORIGIN_OWNER,
            "idea": idea,
            "status": ContributorStatus.INNOVATOR.value,
        }
        uri = reverse(self.api_name, (prepare_contributors.topics[0].id,))
        response = test_app.post(
            uri, data=json.dumps(new_contributor), content_type="application/json"
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response_data == {"topic": ["This field is required."]}

    def test_negative_create_contributor_no_idea(self, prepare_contributors, test_app):
        topic = prepare_contributors.topics[0].id
        new_contributor = {
            "user": TEST_ORIGIN_OWNER,
            "topic": topic,
            "status": ContributorStatus.INNOVATOR.value,
        }
        uri = reverse(self.api_name, (prepare_contributors.topics[0].id,))
        response = test_app.post(
            uri, data=json.dumps(new_contributor), content_type="application/json"
        )
        response_data = response.json()
        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert response_data == {"idea": ["This field is required."]}


@pytest.mark.django_db
class TestContributorsGetUpdateDelete:
    api_name = "ContributorsGetUpdateDelete"

    def test_get_contributor(self, test_app, prepare_contributors):
        existing_contributor = prepare_contributors.contributors[0]
        topic_id = prepare_contributors.topics[0].id
        uri = reverse(
            self.api_name,
            kwargs={"topic_id": str(topic_id), "contributor_id": str(existing_contributor.id)},
        )
        response = test_app.get(uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(existing_contributor.id)

    def test_update_contributor_status(self, test_app, prepare_contributors):
        existing_contributor = prepare_contributors.contributors[0]
        topic_id = prepare_contributors.topics[0].id
        updated_contributor = {"status": ContributorStatus.ACCELERATOR.value}
        uri = reverse(
            self.api_name,
            kwargs={"topic_id": str(topic_id), "contributor_id": str(existing_contributor.id)},
        )
        response = test_app.put(
            uri, json.dumps(updated_contributor), content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["status"] == updated_contributor["status"]
        updated_contributor_obj = Contributor.objects.get(id=existing_contributor.id)
        assert updated_contributor_obj.status == updated_contributor["status"]

    def test_delete_contributor(self, test_app, prepare_contributors):
        existing_contributor = prepare_contributors.contributors[0]
        topic_id = prepare_contributors.topics[0].id
        uri = reverse(
            self.api_name,
            kwargs={"topic_id": str(topic_id), "contributor_id": str(existing_contributor.id)},
        )
        response = test_app.delete(uri, format="json")
        assert response.status_code == status.HTTP_200_OK
        contributor = Contributor.objects.filter(id=existing_contributor.id)
        assert not contributor

import json
import uuid

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from django import test
from django.urls.exceptions import NoReverseMatch

from geo_search_api.apps.notes.models import Note
from geo_search_api.apps.ideas.models import Idea
from geo_search_api.apps.topics.models import TopicStage


@pytest.mark.django_db
class TestLikesConfigurationGet:
    uri = reverse("LikesConfigurationGet")

    def test_configuration_get_unauthorized_negative_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @test.override_settings(LIKES_OBJECT_TYPES={"TypeA": "A", "TypeB": "B"})
    def test_configuration_get_override_positive_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["object_types"] == ["type-a", "type-b"]

    def test_configuration_get_positive_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["object_types"] == ["note", "comment", "idea"]


@pytest.mark.django_db
class TestLikesGetOrCreateOrDeleteView:
    _uri_name = "LikesGetOrCreateOrDelete"
    _uuid = str(uuid.uuid4())

    def test_retrieve_all_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__list(test_app_unauthorized, "note", self._uuid)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_retrieve_all_without_query_params_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "note", self._uuid)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_retrieve_all_with_wrong_object_id_negative_scenario(self, prepare_likes, test_app):
        with pytest.raises(NoReverseMatch):
            self.__list(test_app, "note", "wrong-id")

    def test_retrieve_all_with_wrong_object_type_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "wrong-type", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @test.override_settings(LIKES_OBJECT_TYPES={"TestA": "A"})
    def test_retrieve_all_with_valid_query_params_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "test-a", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_retrieve_all_not_found_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "note", self._uuid)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_retrieve_all_for_note_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "note", prepare_likes.notes[0].id)

        assert response.status_code == status.HTTP_200_OK
        assert body["count"] == 2
        assert body["total_pages"] == 1
        assert len(body["results"]) == 2
        assert body["is_current_user_liked"]

    def test_retrieve_all_for_comment_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "comment", prepare_likes.comments[0].id)

        assert response.status_code == status.HTTP_200_OK
        assert body["count"] == 2
        assert body["total_pages"] == 1
        assert len(body["results"]) == 2
        assert body["is_current_user_liked"]

    def test_retrieve_all_for_idea_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "idea", prepare_likes.ideas[0].id)

        assert response.status_code == status.HTTP_200_OK
        assert body["count"] == 2
        assert body["total_pages"] == 1
        assert len(body["results"]) == 2
        assert body["is_current_user_liked"]

    def test_create_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__create(test_app_unauthorized, "Note", self._uuid)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_create_with_wrong_object_id_negative_scenario(self, prepare_likes, test_app):
        with pytest.raises(NoReverseMatch):
            self.__create(test_app, "note", "wrong-id")

    def test_create_with_wrong_object_type_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__create(test_app, "wrong-type", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @test.override_settings(LIKES_OBJECT_TYPES={"TestA": "A"})
    def test_create_with_valid_query_params_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__create(test_app, "test-a", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_create_not_found_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__create(test_app, "note", self._uuid)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_create_for_note_positive_scenario(self, prepare_notes, test_app):

        body, response = self.__create(test_app, "note", prepare_notes.notes[0].id)
        assert response.status_code == status.HTTP_201_CREATED

        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert body["is_current_user_liked"]

    def test_create_for_note_two_likes_negative_scenario(self, prepare_notes, test_app):
        self.__create(test_app, "note", prepare_notes.notes[0].id)
        body, response = self.__create(test_app, "note", prepare_notes.notes[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "You have already liked this object."

    def test_create_for_comment_positive_scenario(self, prepare_comments, test_app):

        body, response = self.__create(test_app, "comment", prepare_comments.comments[0].id)
        assert response.status_code == status.HTTP_201_CREATED

        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert body["is_current_user_liked"]

    def test_create_for_comment_negative_scenario_topic_status(self, prepare_comments, test_app):
        evaluation_stage, _ = TopicStage.objects.get_or_create(name="Evaluation")
        associated_object = prepare_comments.comments[0].liked_object

        if isinstance(associated_object, Idea):
            topic = associated_object.topic
            topic.stage = evaluation_stage
            topic.save()
            body, response = self.__create(test_app, "comment", prepare_comments.comments[0].id)

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            assert body["detail"] == f"This topic is {evaluation_stage.name}, action not permitted."

    def test_create_for_comment_two_likes_negative_scenario(self, prepare_comments, test_app):
        self.__create(test_app, "comment", prepare_comments.comments[0].id)
        body, response = self.__create(test_app, "comment", prepare_comments.comments[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "You have already liked this object."

    def test_delete_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__delete(test_app_unauthorized, "note", self._uuid)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_delete_without_query_params_negative_scenario(self, prepare_likes, test_app):
        with pytest.raises(NoReverseMatch):
            self.__delete(test_app)

    def test_delete_with_wrong_object_id_negative_scenario(self, prepare_likes, test_app):
        with pytest.raises(NoReverseMatch):
            self.__delete(test_app, "note", "wrong-id")

    def test_delete_with_wrong_object_type_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__delete(test_app, "wrong-type", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @test.override_settings(LIKES_OBJECT_TYPES={"TestA": "A"})
    def test_delete_with_valid_query_params_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__delete(test_app, "test-a", self._uuid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_delete_not_found_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__delete(test_app, "note", self._uuid)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_delete_for_note_positive_scenario(self, prepare_likes, test_app):

        body, response = self.__delete(test_app, "note", prepare_likes.notes[0].id)
        assert response.status_code == status.HTTP_200_OK

        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert not body["is_current_user_liked"]

    def test_delete_for_note_non_existing_like_negative_scenario(self, prepare_likes, test_app):
        self.__delete(test_app, "note", prepare_likes.notes[0].id)
        body, response = self.__delete(test_app, "note", prepare_likes.notes[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "Your like does not exist for this object."

    def test_delete_for_comment_positive_scenario(self, prepare_likes, test_app):

        body, response = self.__delete(test_app, "comment", prepare_likes.comments[0].id)
        assert response.status_code == status.HTTP_200_OK

        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert not body["is_current_user_liked"]

    def test_delete_for_comment_non_existing_like_negative_scenario(self, prepare_likes, test_app):
        self.__delete(test_app, "comment", prepare_likes.comments[0].id)
        body, response = self.__delete(test_app, "comment", prepare_likes.comments[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "Your like does not exist for this object."

    def test_create_for_idea_positive_scenario(self, prepare_ideas, test_app):

        body, response = self.__create(test_app, "idea", prepare_ideas.ideas[0].id)
        assert response.status_code == status.HTTP_201_CREATED
        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert body["is_current_user_liked"]

    def test_create_for_idea_negative_scenario_topic_status(self, prepare_ideas, test_app):
        closed_stage, _ = TopicStage.objects.get_or_create(name="Closed")

        topic = prepare_ideas.ideas[0].topic
        topic.stage = closed_stage
        topic.save()

        body, response = self.__create(test_app, "idea", prepare_ideas.ideas[0].id)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert body["detail"] == f"This topic is {closed_stage.name}, action not permitted."

    def test_create_for_ideas_two_likes_negative_scenario(self, prepare_ideas, test_app):
        self.__create(test_app, "idea", prepare_ideas.ideas[0].id)
        body, response = self.__create(test_app, "idea", prepare_ideas.ideas[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "You have already liked this object."

    def test_create_likes_for_two_ideas_positive_scenario(self, prepare_ideas, test_app):
        body, response = self.__create(test_app, "idea", prepare_ideas.ideas[1].id)
        body2, response2 = self.__create(test_app, "idea", prepare_ideas.ideas[0].id)

        assert response.status_code == status.HTTP_201_CREATED
        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert body["is_current_user_liked"]

        assert response2.status_code == status.HTTP_201_CREATED
        assert body2["count"] == 1
        assert len(body2["results"]) == 1
        assert body2["is_current_user_liked"]

    def test_delete_for_idea_positive_scenario(self, prepare_likes, test_app):

        body, response = self.__delete(test_app, "idea", prepare_likes.ideas[0].id)
        assert response.status_code == status.HTTP_200_OK

        assert body["count"] == 1
        assert len(body["results"]) == 1
        assert not body["is_current_user_liked"]

    def test_delete_for_idea_non_existing_like_negative_scenario(self, prepare_likes, test_app):
        self.__delete(test_app, "idea", prepare_likes.ideas[0].id)
        body, response = self.__delete(test_app, "idea", prepare_likes.ideas[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert body["detail"] == "Your like does not exist for this object."

    def test_retrieve_all_idea_not_found_negative_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, "idea", self._uuid)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Idea.objects.filter(id=self._uuid).exists()

    def __list(self, app, *args):
        response = app.get(reverse(self._uri_name, args))
        return response.json(), response

    def __create(self, app, *args):
        response = app.post(
            reverse(self._uri_name, args),
            data=json.dumps({}),
            content_type="application/json",
        )
        return response.json(), response

    def __delete(self, app, *args):
        response = app.delete(reverse(self._uri_name, args))
        return response.json(), response

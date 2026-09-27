import uuid
import json
import pytest

from rest_framework import status as drf_status
from rest_framework.reverse import reverse as drf_reverse
from django import test as dj_test
from django.urls import exceptions as dj_urls_exceptions

from geo_search_api.apps.notes.models import Note
from geo_search_api.apps.comments.models import Comment
from geo_search_api.apps.topics.models import TopicStage
from tests.test_data import (
    TEST_ORIGIN_OWNER,
)


@pytest.mark.django_db
class TestCommentsConfigurationGet:
    uri = drf_reverse("CommentsConfigurationGet")

    def test_configuration_get_unauthorized_negative_scenario(self, test_app_unauthorized):
        response = test_app_unauthorized.get(self.uri)
        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TypeA": "A", "TypeB": "B"})
    def test_configuration_get_override_positive_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == drf_status.HTTP_200_OK

        data = response.json()
        assert data["object_types"] == ["type-a", "type-b"]

    def test_configuration_get_positive_scenario(self, test_app):
        response = test_app.get(self.uri)
        assert response.status_code == drf_status.HTTP_200_OK

        data = response.json()
        assert data["object_types"] == ["note", "idea"]


@pytest.mark.django_db
class TestCommentsGetOrCreate:
    _uri_name = "CommentsGetOrCreate"
    _uuid = str(uuid.uuid4())

    def test_retrieve_all_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__list(test_app_unauthorized, "note", self._uuid)

        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_retrieve_all_without_query_params_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__list(test_app, "note", self._uuid)
        assert response.status_code == drf_status.HTTP_404_NOT_FOUND

    def test_retrieve_all_with_wrong_object_id_negative_scenario(self, prepare_comments, test_app):
        with pytest.raises(dj_urls_exceptions.NoReverseMatch):
            self.__list(test_app, "note", "wrong-id")

    def test_retrieve_all_with_wrong_object_type_negative_scenario(
        self, prepare_comments, test_app
    ):
        body, response = self.__list(test_app, "wrong-type", self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TestA": "A"})
    def test_retrieve_all_with_valid_query_params_negative_scenario(
        self, prepare_comments, test_app
    ):
        body, response = self.__list(test_app, "test-a", self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_retrieve_all_not_found_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__list(test_app, "note", self._uuid)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_retrieve_all_for_note_positive_scenario(self, prepare_comments, test_app):
        body, response = self.__list(test_app, "note", prepare_comments.notes[0].id)

        assert response.status_code == drf_status.HTTP_200_OK
        assert body["count"] == 4
        assert body["total_pages"] == 1
        assert len(body["results"]) == 4

    def test_retrieve_all_for_note_with_custom_pagination_positive_scenario(
        self, prepare_comments, test_app
    ):
        note = prepare_comments.notes[0]
        comments = note.comments.all()
        # with 1 element per page / first page
        body, response = self.__list(test_app, "note", note.id, query_string="page_size=1")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4
        assert body.get("next") is True
        assert body.get("previous") is False
        assert len(body.get("results")) == 1
        assert body.get("results")[0]["id"] == str(comments[0].id)

        # with 1 element per page / second page
        body, response = self.__list(test_app, "note", note.id, query_string="page_size=1&page=2")
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("count") == 4
        assert body.get("total_pages") == 4
        assert body.get("next")
        assert body.get("previous")
        assert len(body.get("results")) == 1
        assert body.get("results")[0]["id"] == str(comments[1].id)

        # with 2 elements per page / first page
        body, response = self.__list(test_app, "note", note.id, query_string="page_size=2")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4 / 2
        assert body.get("next")
        assert not body.get("previous")
        assert len(body.get("results")) == 2
        assert body.get("results")[0]["id"] == str(comments[0].id)
        assert body.get("results")[1]["id"] == str(comments[1].id)

        # with 2 elements per page / second page
        body, response = self.__list(test_app, "note", note.id, query_string="page_size=2&page=2")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4 / 2
        assert not body.get("next")
        assert body.get("previous")
        assert len(body.get("results")) == 2
        assert body.get("results")[0]["id"] == str(comments[2].id)
        assert body.get("results")[1]["id"] == str(comments[3].id)

    def test_retrieve_all_for_idea_positive_scenario(self, prepare_comments, test_app):
        body, response = self.__list(test_app, "idea", prepare_comments.ideas[0].id)

        assert response.status_code == drf_status.HTTP_200_OK
        assert body["count"] == 4
        assert body["total_pages"] == 1
        assert len(body["results"]) == 4

    def test_retrieve_all_for_idea_with_custom_pagination_positive_scenario(
        self, prepare_comments, test_app
    ):
        idea = prepare_comments.ideas[0]
        comments = idea.comments.all()
        # with 1 element per page / first page
        body, response = self.__list(test_app, "idea", idea.id, query_string="page_size=1")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4
        assert body.get("next") is True
        assert body.get("previous") is False
        assert len(body.get("results")) == 1
        assert body.get("results")[0]["id"] == str(comments[0].id)

        # with 1 element per page / second page
        body, response = self.__list(test_app, "idea", idea.id, query_string="page_size=1&page=2")
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("count") == 4
        assert body.get("total_pages") == 4
        assert body.get("next")
        assert body.get("previous")
        assert len(body.get("results")) == 1
        assert body.get("results")[0]["id"] == str(comments[1].id)

        # with 2 elements per page / first page
        body, response = self.__list(test_app, "idea", idea.id, query_string="page_size=2")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4 / 2
        assert body.get("next")
        assert not body.get("previous")
        assert len(body.get("results")) == 2
        assert body.get("results")[0]["id"] == str(comments[0].id)
        assert body.get("results")[1]["id"] == str(comments[1].id)

        # with 2 elements per page / second page
        body, response = self.__list(test_app, "idea", idea.id, query_string="page_size=2&page=2")
        assert response.status_code == drf_status.HTTP_200_OK

        assert body.get("count") == 4
        assert body.get("total_pages") == 4 / 2
        assert not body.get("next")
        assert body.get("previous")
        assert len(body.get("results")) == 2
        assert body.get("results")[0]["id"] == str(comments[2].id)
        assert body.get("results")[1]["id"] == str(comments[3].id)

    def test_create_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__create(test_app_unauthorized, {}, "note", self._uuid)

        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_create_with_wrong_object_id_negative_scenario(self, prepare_comments, test_app):
        with pytest.raises(dj_urls_exceptions.NoReverseMatch):
            self.__create(test_app, {}, "note", "wrong-id")

    def test_create_with_wrong_object_type_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__create(test_app, {}, "wrong-type", self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TestA": "A"})
    def test_create_with_valid_query_params_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__create(test_app, {}, "test-a", self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_create_not_found_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__create(test_app, {}, "note", self._uuid)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_create_for_note_positive_scenario(self, prepare_notes, test_app):

        body, response = self.__create(
            test_app, {"content": "Lorem Ipsum"}, "note", prepare_notes.notes[0].id
        )
        assert response.status_code == drf_status.HTTP_201_CREATED

        assert body.get("content") == "Lorem Ipsum"
        assert body.get("owner") == TEST_ORIGIN_OWNER
        assert Comment.objects.filter(id=body.get("id")).exists()

    def test_create_reply_for_note_with_wrong_parent_id_negative_scenario(
        self, prepare_comments, test_app
    ):
        body, response = self.__create(
            test_app,
            {"content": "Lorem Ipsum", "parent_id": self._uuid},
            "note",
            prepare_comments.notes[0].id,
        )

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body == {"parent_id": [f'Invalid pk "{self._uuid}" - object does not exist.']}

    def test_create_reply_for_note_positive_scenario(self, prepare_comments, test_app):
        body, response = self.__create(
            test_app,
            {"content": "Lorem Ipsum", "parent_id": str(prepare_comments.comments[0].id)},
            "note",
            prepare_comments.notes[0].id,
        )

        assert response.status_code == drf_status.HTTP_201_CREATED

        assert body.get("content") == "Lorem Ipsum"
        assert body.get("owner") == TEST_ORIGIN_OWNER
        assert body.get("parent_id") == str(prepare_comments.comments[0].id)

        reply_comment = Comment.objects.get(id=body.get("id"))
        assert reply_comment.content == "Lorem Ipsum"
        assert reply_comment.owner == TEST_ORIGIN_OWNER
        assert str(reply_comment.parent_id.id) == str(prepare_comments.comments[0].id)

    def test_create_for_idea_positive_scenario(self, prepare_ideas, test_app):

        body, response = self.__create(
            test_app, {"content": "Lorem Ipsum"}, "idea", prepare_ideas.ideas[0].id
        )
        assert response.status_code == drf_status.HTTP_201_CREATED

        assert body.get("content") == "Lorem Ipsum"
        assert body.get("owner") == TEST_ORIGIN_OWNER
        assert Comment.objects.filter(id=body.get("id")).exists()

    def test_create_for_idea_negative_scenario_topic_status(self, prepare_ideas, test_app):
        idea = prepare_ideas.ideas[0]
        topic = idea.topic
        evaluation_stage, _ = TopicStage.objects.get_or_create(name="Evaluation")

        topic.stage = evaluation_stage
        topic.save()

        body, response = self.__create(test_app, {"content": "Lorem Ipsum"}, "idea", idea.id)
        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["detail"] == f"This topic is {evaluation_stage.name}, action not permitted."

    def test_create_reply_for_idea_with_wrong_parent_id_negative_scenario(
        self, prepare_comments, test_app
    ):
        body, response = self.__create(
            test_app,
            {"content": "Lorem Ipsum", "parent_id": self._uuid},
            "idea",
            prepare_comments.ideas[0].id,
        )

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body == {"parent_id": [f'Invalid pk "{self._uuid}" - object does not exist.']}

    def test_create_reply_for_idea_positive_scenario(self, prepare_comments, test_app):
        body, response = self.__create(
            test_app,
            {"content": "Lorem Ipsum", "parent_id": str(prepare_comments.comments[0].id)},
            "idea",
            prepare_comments.ideas[0].id,
        )

        assert response.status_code == drf_status.HTTP_201_CREATED

        assert body.get("content") == "Lorem Ipsum"
        assert body.get("owner") == TEST_ORIGIN_OWNER
        assert body.get("parent_id") == str(prepare_comments.comments[0].id)

        reply_comment = Comment.objects.get(id=body.get("id"))
        assert reply_comment.content == "Lorem Ipsum"
        assert reply_comment.owner == TEST_ORIGIN_OWNER
        assert str(reply_comment.parent_id.id) == str(prepare_comments.comments[0].id)

    def __list(self, app, *args, **kwargs):
        response = app.get(
            drf_reverse(self._uri_name, args), QUERY_STRING=kwargs.get("query_string")
        )
        return response.json(), response

    def __create(self, app, data: dict, *args):
        response = app.post(
            drf_reverse(self._uri_name, args),
            data=json.dumps(data),
            content_type="application/json",
        )
        return response.json(), response


@pytest.mark.django_db
class TestCommentGetOrUpdateOrDelete:
    _uri_name = "CommentGetOrUpdateOrDelete"
    _uuid = str(uuid.uuid4())

    def test_get_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__get(test_app_unauthorized, "note", self._uuid, self._uuid)

        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_get_with_wrong_object_id_negative_scenario(self, prepare_comments, test_app):
        with pytest.raises(dj_urls_exceptions.NoReverseMatch):
            self.__get(test_app, "note", "wrong-id", self._uuid)

    def test_get_with_wrong_object_type_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__get(test_app, "wrong-type", self._uuid, self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TestA": "A"})
    def test_get_with_valid_query_params_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__get(test_app, "test-a", self._uuid, self._uuid)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_get_not_found_with_fake_note_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__get(test_app, "note", self._uuid, prepare_comments.comments[0].id)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "Not found."
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_get_not_found_with_fake_comment_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__get(test_app, "note", prepare_comments.notes[0].id, self._uuid)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "The comment does not exists."
        assert not Comment.objects.filter(id=self._uuid).exists()

    def test_get_for_note_positive_scenario(self, prepare_comments, test_app):
        # get own comment
        body, response = self.__get(
            test_app, "note", prepare_comments.notes[0].id, prepare_comments.comments[0].id
        )
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("id") == str(prepare_comments.comments[0].id)
        assert body.get("owner") == prepare_comments.comments[0].owner

        # get comment by id with another owner
        body, response = self.__get(
            test_app, "note", prepare_comments.notes[0].id, prepare_comments.comments[3].id
        )
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("id") == str(prepare_comments.comments[3].id)
        assert body.get("owner") == prepare_comments.comments[3].owner

    def test_get_for_note_with_likes_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__get(
            test_app, "note", prepare_likes.notes[0].id, prepare_likes.comments[0].id
        )

        assert response.status_code == drf_status.HTTP_200_OK
        assert "likes" in body
        assert body["likes"]["count"] == 2
        assert body["likes"]["is_current_user_liked"]

    def test_get_for_idea_positive_scenario(self, prepare_comments, test_app):
        idea = prepare_comments.ideas[0]
        comments = idea.comments.all()
        # get own comment
        body, response = self.__get(test_app, "idea", idea.id, comments[0].id)
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("id") == str(comments[0].id)
        assert body.get("owner") == comments[0].owner

        # get comment by id with another owner
        body, response = self.__get(test_app, "idea", idea.id, comments[3].id)
        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("id") == str(comments[3].id)
        assert body.get("owner") == comments[3].owner

    def test_update_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__update(test_app_unauthorized, {}, "note", self._uuid, self._uuid)

        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_update_with_wrong_object_id_negative_scenario(self, prepare_comments, test_app):
        with pytest.raises(dj_urls_exceptions.NoReverseMatch):
            self.__update(test_app, {}, "note", "wrong-id", prepare_comments.comments[0].id)

    def test_update_with_wrong_object_type_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__update(
            test_app, {}, "wrong-type", prepare_comments.notes[0].id, my_comment.id
        )

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TestA": "A"})
    def test_update_with_valid_query_params_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__update(test_app, {}, "test-a", my_comment.object_id, my_comment.id)

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_update_not_found_with_fake_note_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__update(test_app, {}, "note", self._uuid, my_comment.id)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "Not found."
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_update_not_found_with_fake_comment_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__update(
            test_app, {}, "note", prepare_comments.notes[0].id, self._uuid
        )

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "The comment does not exists."
        assert not Comment.objects.filter(id=self._uuid).exists()

    def test_update_someone_else_comment_negative_scenario(self, prepare_comments, test_app):
        alien_comment = [
            _ for _ in filter(lambda c: c.owner != TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__update(
            test_app,
            {"content": "Updated content"},
            alien_comment.object_type.name,
            alien_comment.object_id,
            alien_comment.id,
        )
        assert response.status_code == drf_status.HTTP_403_FORBIDDEN

        comment = Comment.objects.get(id=alien_comment.id)
        assert comment.content != "Updated content"

    def test_update_own_comment_positive_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__update(
            test_app,
            {"content": "Updated content"},
            my_comment.object_type.name,
            my_comment.object_id,
            my_comment.id,
        )

        assert response.status_code == drf_status.HTTP_200_OK
        assert body.get("id") == str(my_comment.id)
        assert body.get("owner") == my_comment.owner
        assert body.get("content") == "Updated content"

        comment = Comment.objects.get(id=body.get("id"))
        assert comment.content == "Updated content"

    def test_delete_unauthorized_negative_scenario(self, test_app_unauthorized):
        body, response = self.__delete(test_app_unauthorized, "note", self._uuid, self._uuid)

        assert response.status_code == drf_status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_delete_with_wrong_object_id_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        with pytest.raises(dj_urls_exceptions.NoReverseMatch):
            self.__delete(test_app, "note", "wrong-id", prepare_comments.notes[0].id, my_comment.id)

    def test_delete_with_wrong_object_type_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][1]
        body, response = self.__delete(
            test_app, "wrong-type", prepare_comments.notes[0].id, my_comment.id
        )

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Unsupported the object type"

    @dj_test.override_settings(COMMENTS_OBJECT_TYPES={"TestA": "A"})
    def test_delete_with_valid_query_params_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__delete(
            test_app, "test-a", prepare_comments.notes[0].id, my_comment.id
        )

        assert response.status_code == drf_status.HTTP_400_BAD_REQUEST
        assert body["object_type"][0] == "Wrong the object import path"

    def test_delete_not_found_with_fake_note_negative_scenario(self, prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__delete(test_app, "note", self._uuid, my_comment.id)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "Not found."
        assert not Note.objects.filter(id=self._uuid).exists()

    def test_delete_not_found_with_fake_comment_negative_scenario(self, prepare_comments, test_app):
        body, response = self.__delete(test_app, "note", prepare_comments.notes[0].id, self._uuid)

        assert response.status_code == drf_status.HTTP_404_NOT_FOUND
        assert body["detail"] in "The comment does not exists."
        assert not Comment.objects.filter(id=self._uuid).exists()

    def test_delete_fails_when_someone_else_comment_negative_scenario(
        self, prepare_comments, test_app
    ):
        alien_comment = [
            _ for _ in filter(lambda c: c.owner != TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        body, response = self.__delete(
            test_app, alien_comment.object_type.name, alien_comment.object_id, alien_comment.id
        )
        assert response.status_code == drf_status.HTTP_403_FORBIDDEN
        assert Comment.objects.filter(id=alien_comment.id).exists()

    def test_delete_own_comment_positive_scenario(self, prepare_comments, test_app):
        # Only the first comment has replies
        my_comment = prepare_comments.comments[0]
        my_comment.owner = TEST_ORIGIN_OWNER
        my_comment.save()

        replies = list(my_comment.replies.all())
        body, response = self.__delete(
            test_app, my_comment.object_type.name, my_comment.object_id, my_comment.id
        )

        assert response.status_code == drf_status.HTTP_200_OK
        assert not Comment.objects.filter(id=my_comment.id).exists()
        # check that all replies for specific are removed
        assert not Comment.objects.filter(id=replies[0].id).exists()
        assert not Comment.objects.filter(id=replies[1].id).exists()

    def test_delete_own_reply_positive_scenario(self, prepare_comments, test_app):

        # Only the first comment has replies
        my_comment = prepare_comments.comments[0]
        my_comment.owner = TEST_ORIGIN_OWNER
        my_comment.save()

        my_reply = my_comment.replies.all()[0]
        my_reply.owner = TEST_ORIGIN_OWNER
        my_reply.save()

        body, response = self.__delete(
            test_app, my_comment.object_type.name, my_comment.object_id, my_reply.id
        )

        assert response.status_code == drf_status.HTTP_200_OK
        assert not Comment.objects.filter(id=my_reply.id).exists()

    def __get(self, app, *args):
        response = app.get(drf_reverse(self._uri_name, args))
        return response.json(), response

    def __update(self, app, data: dict, *args):
        response = app.put(
            drf_reverse(self._uri_name, args),
            data=json.dumps(data),
            content_type="application/json",
        )
        return response.json(), response

    def __delete(self, app, *args):
        response = app.delete(drf_reverse(self._uri_name, args))
        return response.json(), response

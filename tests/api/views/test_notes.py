import json
import uuid

import pytest
from rest_framework import status
from rest_framework.reverse import reverse

from geo_search_api.apps.notes.models import Note
from geo_search_api.apps.likes.models import Like
from geo_search_api.apps.comments.models import Comment
from tests.test_data import (
    TEST_NOTES,
    POST_UUID_1,
    POST_UUID_2,
    POST_UUID_3,
    IDEA_UUID,
    TEST_ORIGIN_OWNER,
    TEST_ANOTHER_OWNER,
)


@pytest.mark.django_db
class TestNotesGetOrCreate:
    @staticmethod
    def test_get_all_notes_positive_scenario(prepare_notes, test_app):
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(TEST_NOTES)
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == len(TEST_NOTES)
        # sorted by date from newest to oldest
        assert response_data.get("results")[0]["id"] == IDEA_UUID
        assert response_data.get("results")[1]["id"] == POST_UUID_3
        assert response_data.get("results")[2]["id"] == POST_UUID_2
        assert response_data.get("results")[3]["id"] == POST_UUID_1

    @staticmethod
    def test_get_all_notes_have_comments_count_positive_scenario(prepare_comments, test_app):
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data.get("count") == len(prepare_comments.notes)
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert response_data.get("results")[0]["id"] == prepare_comments.notes[-1].id
        assert response_data.get("results")[-1]["comments_count"] == 6

    @staticmethod
    def test_get_all_notes_with_different_case_types(prepare_notes, test_app):
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("total_pages")
        assert response_data["results"][0].get("created_at")
        assert response_data["results"][0].get("updated_at")

        response = test_app.get(url, HTTP_X_CASE="camelcase")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("totalPages")
        assert response_data["results"][0].get("createdAt")
        assert response_data["results"][0].get("updatedAt")

    @staticmethod
    def test_get_all_notes_with_custom_pagination_positive_scenario(prepare_notes, test_app):
        # with 1 element per page / first page
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url, QUERY_STRING="page_size=1")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(TEST_NOTES)
        assert response_data.get("total_pages") == len(TEST_NOTES)
        assert response_data.get("next") is True
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 1
        assert response_data.get("results")[0]["id"] == IDEA_UUID

        # with 1 element per page / second page
        response = test_app.get(url, QUERY_STRING="page_size=1&page=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(TEST_NOTES)
        assert response_data.get("total_pages") == len(TEST_NOTES)
        assert response_data.get("next") is True
        assert response_data.get("previous") is True
        assert len(response_data.get("results")) == 1
        assert response_data.get("results")[0]["id"] == POST_UUID_3

        # with 2 elements per page / first page
        response = test_app.get(url, QUERY_STRING="page_size=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(TEST_NOTES)
        assert response_data.get("total_pages") == len(TEST_NOTES) / 2
        assert response_data.get("next") is True
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["id"] == IDEA_UUID
        assert response_data.get("results")[1]["id"] == POST_UUID_3

        # with 2 elements per page / second page
        response = test_app.get(url, QUERY_STRING="page_size=2&page=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(TEST_NOTES)
        assert response_data.get("total_pages") == len(TEST_NOTES) / 2
        assert response_data.get("next") is False
        assert response_data.get("previous") is True
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["id"] == POST_UUID_2
        assert response_data.get("results")[1]["id"] == POST_UUID_1

    @staticmethod
    def test_get_all_notes_with_specified_category_positive_scenario(prepare_notes, test_app):
        # Post category
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url, QUERY_STRING="category=Post")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == 3
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 3
        assert response_data.get("results")[0]["id"] == POST_UUID_3
        assert response_data.get("results")[1]["id"] == POST_UUID_2
        assert response_data.get("results")[2]["id"] == POST_UUID_1

        # Post category / with pagination
        response = test_app.get(url, QUERY_STRING="category=Post&page_size=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == 3
        assert response_data.get("total_pages") == 2
        assert response_data.get("next") is True
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["id"] == POST_UUID_3
        assert response_data.get("results")[1]["id"] == POST_UUID_2

        # Idea category
        response = test_app.get(url, QUERY_STRING="category=Idea")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == 1
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 1
        assert response_data.get("results")[0]["id"] == IDEA_UUID

    @staticmethod
    def test_get_all_notes_with_specified_user_positive_scenario(prepare_notes, test_app):
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url, QUERY_STRING=f"owner={TEST_ORIGIN_OWNER}")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == 3
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 3
        assert response_data.get("results")[0]["owner"] == TEST_ORIGIN_OWNER
        assert response_data.get("results")[1]["owner"] == TEST_ORIGIN_OWNER
        assert response_data.get("results")[2]["owner"] == TEST_ORIGIN_OWNER

    @staticmethod
    def test_get_all_notes_with_specified_user_and_category_positive_scenario(
        prepare_notes, test_app
    ):
        url = reverse("NotesGetOrCreateView")
        response = test_app.get(url, QUERY_STRING=f"category=Post&owner={TEST_ORIGIN_OWNER}")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == 2
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["owner"] == TEST_ORIGIN_OWNER
        assert response_data.get("results")[0]["category"] == "Post"
        assert response_data.get("results")[1]["owner"] == TEST_ORIGIN_OWNER
        assert response_data.get("results")[1]["category"] == "Post"

    @staticmethod
    def test_create_notes_positive_scenario(prepare_notes, test_app):
        url = reverse("NotesGetOrCreateView")
        new_post = {"content": "my new test content", "category": "Post"}
        response = test_app.post(url, data=json.dumps(new_post), content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("content") == "my new test content"
        assert response_data.get("category") == "Post"
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        note_data = Note.objects.get(id=response_data.get("id"))
        assert note_data.content == "my new test content"
        assert note_data.owner == TEST_ORIGIN_OWNER

    @staticmethod
    def test_create_notes_fails_with_wrong_category(prepare_notes, test_app):
        url = reverse("NotesGetOrCreateView")
        wrong_category = "wrong category"
        new_post = {"content": "my new test content", "category": wrong_category}
        response = test_app.post(url, data=json.dumps(new_post), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {"category": [f'"{wrong_category}" is not a valid choice.']}


@pytest.mark.django_db
class TestNoteGetOrUpdateView:
    @staticmethod
    def test_get_note_by_id_positive_scenario(prepare_notes, test_app):
        # get own note
        url = reverse("NoteGetOrUpdateView", (POST_UUID_1,))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == POST_UUID_1
        assert response_data.get("owner") == TEST_ORIGIN_OWNER

        # get by id note with another owner
        url = reverse("NoteGetOrUpdateView", (POST_UUID_3,))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == POST_UUID_3
        assert response_data.get("owner") == TEST_ANOTHER_OWNER

    @staticmethod
    def test_get_note_by_id_with_likes_positive_scenario(prepare_likes, test_app):
        url = reverse("NoteGetOrUpdateView", (prepare_likes.notes[0].id,))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert "likes" in response_data
        assert response_data["likes"]["count"] == 2
        assert response_data["likes"]["is_current_user_liked"]

    @staticmethod
    def test_get_note_by_id_delete_likes_before_retrieve_positive_scenario(
        prepare_likes,
        test_app,
    ):
        test_app.delete(
            reverse("NoteLikesView", (prepare_likes.notes[0].id,)),
            data=json.dumps({}),
            content_type="application/json",
        )
        response = test_app.get(reverse("NoteGetOrUpdateView", (prepare_likes.notes[0].id,)))
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data["likes"]["count"] == 1
        assert not response_data["likes"]["is_current_user_liked"]

    @staticmethod
    def test_get_note_by_id_fails_with_wrong_note_id(prepare_notes, test_app):
        wrong_note_id = str(uuid.uuid4())
        url = reverse("NoteGetOrUpdateView", (wrong_note_id,))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_update_own_note_positive_scenario(prepare_notes, test_app):
        url = reverse("NoteGetOrUpdateView", (POST_UUID_1,))
        updated_post = {"content": "new updated content"}
        response = test_app.put(url, data=json.dumps(updated_post), content_type="application/json")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == POST_UUID_1
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        assert response_data.get("content") == "new updated content"

        note_data = Note.objects.get(id=response_data.get("id"))
        assert note_data.content == "new updated content"

    @staticmethod
    def test_update_note_fails_with_wrong_note_id(prepare_notes, test_app):
        wrong_note_id = str(uuid.uuid4())
        url = reverse("NoteGetOrUpdateView", (wrong_note_id,))
        updated_post = {"content": "new updated content"}
        response = test_app.put(url, data=json.dumps(updated_post), content_type="application/json")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_update_fails_when_someone_else_note(prepare_notes, test_app):
        url = reverse("NoteGetOrUpdateView", (POST_UUID_3,))
        updated_post = {"content": "new updated content"}
        response = test_app.put(url, data=json.dumps(updated_post), content_type="application/json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

        note_data = Note.objects.get(id=POST_UUID_3)
        assert note_data.content != "new updated content"

    @staticmethod
    def test_delete_own_note_positive_scenario(prepare_notes, test_app):
        url = reverse("NoteGetOrUpdateView", (POST_UUID_1,))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert not Note.objects.filter(id=POST_UUID_1).exists()

    @staticmethod
    def test_delete_fails_when_someone_else_note(prepare_notes, test_app):
        url = reverse("NoteGetOrUpdateView", (POST_UUID_3,))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Note.objects.filter(id=POST_UUID_3).exists()

    @staticmethod
    def test_delete_fails_with_wrong_note_id(prepare_notes, test_app):
        wrong_note_id = str(uuid.uuid4())
        url = reverse("NoteGetOrUpdateView", (wrong_note_id,))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Note.objects.filter(id=POST_UUID_3).exists()


@pytest.mark.django_db
class TestNoteLikesView:

    _uri_name = "NoteLikesView"
    _fake_note_id = str(uuid.uuid4())

    def test_list_401_response(self, test_app_unauthorized):
        body, response = self.__list(test_app_unauthorized, POST_UUID_1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_list_404_response_with_wrong_note_id(self, prepare_notes, test_app):
        body, response = self.__list(test_app, self._fake_note_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_list_200_response_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__list(test_app, prepare_likes.notes[0].id)

        assert response.status_code == status.HTTP_200_OK
        assert body["is_current_user_liked"]
        assert body["count"] == 2
        assert body["total_pages"] == 1
        assert len(body["results"]) == 2

    def test_create_401_response(self, test_app_unauthorized):
        body, response = self.__create(test_app_unauthorized, POST_UUID_1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_create_404_response_with_wrong_note_id(self, prepare_notes, test_app):
        body, response = self.__create(test_app, self._fake_note_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_create_201_response_positive_scenario(self, prepare_notes, test_app):
        _, response = self.__create(test_app, POST_UUID_1)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_json_body_count(self, prepare_notes, test_app):
        body, _ = self.__create(test_app, POST_UUID_1)

        assert "count" in body
        assert body.get("count") == 1

    def test_create_json_body_is_current_user_liked(self, prepare_notes, test_app):
        body, _ = self.__create(test_app, POST_UUID_1)

        assert "is_current_user_liked" in body
        assert body.get("is_current_user_liked")

    def test_create_json_body_results(self, prepare_notes, test_app):
        body, _ = self.__create(test_app, POST_UUID_1)

        assert "results" in body

    def test_create_two_likes_positive_scenario(self, prepare_notes, test_app):
        self.__create(test_app, POST_UUID_1)
        body, response = self.__create(test_app, POST_UUID_1)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in body

    def test_delete_401_response(self, test_app_unauthorized):
        body, response = self.__delete(test_app_unauthorized, POST_UUID_1)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_delete_404_response_with_wrong_note_id(self, prepare_notes, test_app):
        body, response = self.__delete(test_app, self._fake_note_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body
        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_delete_200_response_positive_scenario(self, prepare_likes, test_app):
        _, response = self.__delete(test_app, prepare_likes.notes[0].id)

        assert response.status_code == status.HTTP_200_OK
        assert not Like.objects.filter(object_id=POST_UUID_1, user_id="test_id").exists()

    def test_delete_json_body_count(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id)

        assert "count" in body
        assert body.get("count") == 1

    def test_delete_json_body_is_current_user_liked(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id)

        assert "is_current_user_liked" in body
        assert not body.get("is_current_user_liked")

    def test_delete_json_body_results(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id)

        assert "results" in body

    def test_delete_non_existing_like(self, prepare_likes, test_app):
        _, _ = self.__delete(test_app, prepare_likes.notes[0].id)
        body, response = self.__delete(test_app, prepare_likes.notes[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in body

    def __list(self, app, note_id):
        response = app.get(reverse(self._uri_name, (note_id,)))
        return response.json(), response

    def __create(self, app, note_id):
        response = app.post(
            reverse(self._uri_name, (note_id,)),
            data=json.dumps({}),
            content_type="application/json",
        )
        return response.json(), response

    def __delete(self, app, note_id):
        response = app.delete(
            reverse(self._uri_name, (note_id,)),
            data=json.dumps({}),
            content_type="application/json",
        )
        return response.json(), response


@pytest.mark.django_db
class TestCommentLikesView:

    _uri_name = "CommentLikesView"
    _fake_note_id = str(uuid.uuid4())
    _fake_comment_id = str(uuid.uuid4())

    def test_list_401_response(self, test_app_unauthorized):
        body, response = self.__list(
            test_app_unauthorized, self._fake_note_id, self._fake_comment_id
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_list_404_response_with_wrong_note_id(self, prepare_comments, test_app):
        body, response = self.__list(test_app, self._fake_note_id, prepare_comments.comments[0].id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_list_404_response_with_wrong_comment_id(self, prepare_comments, test_app):
        body, response = self.__list(test_app, POST_UUID_1, self._fake_comment_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Comment.objects.filter(id=self._fake_comment_id).exists()

    def test_list_404_response_for_note_without_comments(self, prepare_likes, test_app):
        # Create a comment for the second note.
        comment = prepare_likes.notes[1].comments.create(
            content="Lorem ipsum", owner=TEST_ORIGIN_OWNER
        )

        # But request send for the first note and the second comment.
        body, response = self.__list(test_app, prepare_likes.notes[0].id, comment.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

    def test_list_200_response_positive_scenario(self, prepare_likes, test_app):
        body, response = self.__list(
            test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id
        )

        assert response.status_code == status.HTTP_200_OK
        assert body["is_current_user_liked"]
        assert body["count"] == 2
        assert body["total_pages"] == 1
        assert len(body["results"]) == 2

    def test_create_401_response(self, test_app_unauthorized):
        body, response = self.__create(test_app_unauthorized, POST_UUID_1, self._fake_comment_id)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_create_404_response_with_wrong_note_id(self, prepare_comments, test_app):
        body, response = self.__create(
            test_app, self._fake_note_id, prepare_comments.comments[0].id
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_create_404_response_with_wrong_comment_id(self, prepare_comments, test_app):
        body, response = self.__create(test_app, POST_UUID_1, self._fake_comment_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Comment.objects.filter(id=self._fake_comment_id).exists()

    def test_create_404_response_for_note_without_comments(self, prepare_likes, test_app):
        # Create a comment for the second note.
        comment = prepare_likes.notes[1].comments.create(
            content="Lorem ipsum", owner=TEST_ORIGIN_OWNER
        )

        # But request send for the first note and the second comment.
        body, response = self.__create(test_app, prepare_likes.notes[0].id, comment.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

    def test_create_201_response_positive_scenario(self, prepare_comments, test_app):
        _, response = self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)
        assert response.status_code == status.HTTP_201_CREATED

    def test_create_json_body_count(self, prepare_comments, test_app):
        body, _ = self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)

        assert "count" in body
        assert body.get("count") == 1

    def test_create_json_body_is_current_user_liked(self, prepare_comments, test_app):
        body, _ = self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)

        assert "is_current_user_liked" in body
        assert body.get("is_current_user_liked")

    def test_create_json_body_results(self, prepare_comments, test_app):
        body, _ = self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)

        assert "results" in body

    def test_create_two_likes_positive_scenario(self, prepare_comments, test_app):
        self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)
        body, response = self.__create(test_app, POST_UUID_1, prepare_comments.comments[0].id)

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in body

    def test_delete_401_response(self, test_app_unauthorized):
        body, response = self.__delete(test_app_unauthorized, POST_UUID_1, self._fake_comment_id)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in body

    def test_delete_404_response_with_wrong_note_id(self, prepare_likes, test_app):
        body, response = self.__delete(test_app, self._fake_note_id, prepare_likes.comments[0].id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Note.objects.filter(id=self._fake_note_id).exists()

    def test_delete_404_response_with_wrong_comment_id(self, prepare_likes, test_app):
        body, response = self.__create(test_app, prepare_likes.notes[0].id, self._fake_comment_id)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

        assert not Comment.objects.filter(id=self._fake_comment_id).exists()

    def test_delete_404_response_for_note_without_comments(self, prepare_likes, test_app):
        # Get the second note
        comment = prepare_likes.notes[1].comments.create(
            content="Lorem ipsum", owner=TEST_ORIGIN_OWNER
        )

        # But request send for the first note and the second comment.
        body, response = self.__delete(test_app, prepare_likes.notes[0].id, comment.id)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "detail" in body

    def test_delete_200_response_positive_scenario(self, prepare_likes, test_app):
        _, response = self.__delete(
            test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id
        )

        assert response.status_code == status.HTTP_200_OK
        assert not Like.objects.filter(
            object_id=prepare_likes.comments[0].id, user_id="test_id"
        ).exists()

    def test_delete_json_body_count(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id)

        assert "count" in body
        assert body.get("count") == 1

    def test_delete_json_body_is_current_user_liked(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id)

        assert "is_current_user_liked" in body
        assert not body.get("is_current_user_liked")

    def test_delete_json_body_results(self, prepare_likes, test_app):
        body, _ = self.__delete(test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id)

        assert "results" in body

    def test_delete_non_existing_like(self, prepare_likes, test_app):
        _, _ = self.__delete(test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id)
        body, response = self.__delete(
            test_app, prepare_likes.notes[0].id, prepare_likes.comments[0].id
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "detail" in body

    def __list(self, app, note_id, comment_id):
        response = app.get(
            reverse(
                self._uri_name,
                (
                    note_id,
                    comment_id,
                ),
            )
        )
        return response.json(), response

    def __create(self, app, note_id, comment_id):
        response = app.post(
            reverse(
                self._uri_name,
                (
                    note_id,
                    comment_id,
                ),
            ),
            data=json.dumps({}),
            content_type="application/json",
        )
        return response.json(), response

    def __delete(self, app, note_id, comment_id):
        response = app.delete(
            reverse(
                self._uri_name,
                (
                    note_id,
                    comment_id,
                ),
            ),
            data=json.dumps({}),
            content_type="application/json",
        )
        return response.json(), response


@pytest.mark.django_db
class TestCommentsGetOrCreate:
    @staticmethod
    def test_get_all_comments_positive_scenario(prepare_comments, test_app):

        note = prepare_comments.notes[0]
        comments = note.comments.filter(parent_id=None).all()
        replies = comments[0].replies.all()

        url = reverse("CommentsGetOrCreateView", (note.id,))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(comments)
        assert response_data.get("total_pages") == 1
        assert response_data.get("next") is False
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == len(comments)
        # sorted by date from oldest to newest
        assert response_data.get("results")[0]["id"] == str(comments[0].id)
        assert response_data.get("results")[1]["id"] == str(comments[1].id)
        assert response_data.get("results")[2]["id"] == str(comments[2].id)
        assert response_data.get("results")[3]["id"] == str(comments[3].id)
        # check comment replies
        replies_data = response_data.get("results")[0]["replies"]
        assert len(replies_data) == len(replies)
        assert replies_data[0]["id"] == str(replies[0].id)
        assert replies_data[1]["id"] == str(replies[1].id)

    @staticmethod
    def test_get_all_comments_with_custom_pagination_positive_scenario(prepare_comments, test_app):
        note = prepare_comments.notes[0]
        comments = note.comments.filter(parent_id=None).all()
        # with 1 element per page / first page
        url = reverse("CommentsGetOrCreateView", (note.id,))
        response = test_app.get(url, QUERY_STRING="page_size=1")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(comments)
        assert response_data.get("total_pages") == len(comments)
        assert response_data.get("next") is True
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 1
        assert response_data.get("results")[0]["id"] == str(comments[0].id)

        # with 1 element per page / second page
        response = test_app.get(url, QUERY_STRING="page_size=1&page=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(comments)
        assert response_data.get("total_pages") == len(comments)
        assert response_data.get("next") is True
        assert response_data.get("previous") is True
        assert len(response_data.get("results")) == 1
        assert response_data.get("results")[0]["id"] == str(comments[1].id)

        # with 2 elements per page / first page
        response = test_app.get(url, QUERY_STRING="page_size=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(comments)
        assert response_data.get("total_pages") == len(comments) / 2
        assert response_data.get("next") is True
        assert response_data.get("previous") is False
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["id"] == str(comments[0].id)
        assert response_data.get("results")[1]["id"] == str(comments[1].id)

        # with 2 elements per page / second page
        response = test_app.get(url, QUERY_STRING="page_size=2&page=2")
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("count") == len(comments)
        assert response_data.get("total_pages") == len(comments) / 2
        assert response_data.get("next") is False
        assert response_data.get("previous") is True
        assert len(response_data.get("results")) == 2
        assert response_data.get("results")[0]["id"] == str(comments[2].id)
        assert response_data.get("results")[1]["id"] == str(comments[3].id)

    @staticmethod
    def test_create_comments_positive_scenario(prepare_comments, test_app):
        url = reverse("CommentsGetOrCreateView", (POST_UUID_1,))
        new_comment = {"content": "my test content"}
        response = test_app.post(url, data=json.dumps(new_comment), content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("content") == "my test content"
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        comment_data = Comment.objects.get(id=response_data.get("id"))
        assert comment_data.content == "my test content"
        assert comment_data.owner == TEST_ORIGIN_OWNER

    @staticmethod
    def test_create_reply_positive_scenario(prepare_comments, test_app):
        comment = prepare_comments.comments[3]
        url = reverse("CommentsGetOrCreateView", (POST_UUID_1,))

        new_comment = {"content": "my test reply content", "parent_id": comment.id}
        response = test_app.post(url, data=json.dumps(new_comment), content_type="application/json")
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert response_data.get("content") == "my test reply content"
        assert response_data.get("owner") == TEST_ORIGIN_OWNER
        assert response_data.get("parent_id") == str(comment.id)
        comment_data = Comment.objects.get(id=response_data.get("id"))
        assert comment_data.content == "my test reply content"
        assert comment_data.owner == TEST_ORIGIN_OWNER
        assert str(comment_data.parent_id.id) == comment.id

    @staticmethod
    def test_create_reply_fails_with_wrong_parent_id(prepare_comments, test_app):
        url = reverse("CommentsGetOrCreateView", (POST_UUID_1,))
        wrong_uuid = str(uuid.uuid4())
        new_comment = {"content": "my test reply content", "parent_id": wrong_uuid}
        response = test_app.post(url, data=json.dumps(new_comment), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            "parent_id": [f'Invalid pk "{wrong_uuid}" - object does not exist.']
        }

    @staticmethod
    def test_create_reply_fails_with_wrong_note_id(prepare_comments, test_app):
        wrong_note_id = str(uuid.uuid4())
        url = reverse("CommentsGetOrCreateView", (wrong_note_id,))
        new_comment = {
            "content": "my test reply content",
            "parent_id": prepare_comments.comments[3].id,
        }
        response = test_app.post(url, data=json.dumps(new_comment), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {
            "object_id": ["Parent comment and reply should have the same object id."]
        }

    @staticmethod
    def test_create_reply_fails_with_wrong_parent_id_type(prepare_comments, test_app):
        url = reverse("CommentsGetOrCreateView", (POST_UUID_1,))
        not_uuid_string = "some not uuid string"
        new_comment = {"content": "my test reply content", "parent_id": not_uuid_string}
        response = test_app.post(url, data=json.dumps(new_comment), content_type="application/json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data == {"parent_id": [f"“{not_uuid_string}” is not a valid UUID."]}


@pytest.mark.django_db
class TestCommentGetOrUpdateView:
    @staticmethod
    def test_get_comment_by_id_positive_scenario(prepare_comments, test_app):
        my_comment = [
            _
            for _ in filter(
                lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.notes[0].comments.all()
            )
        ][0]
        # get own comment
        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, my_comment.id))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == str(my_comment.id)
        assert response_data.get("owner") == TEST_ORIGIN_OWNER

        alien_comment = [
            _
            for _ in filter(
                lambda c: c.owner != TEST_ORIGIN_OWNER, prepare_comments.notes[0].comments.all()
            )
        ][0]
        # get comment by id with another owner
        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, alien_comment.id))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == str(alien_comment.id)
        assert response_data.get("owner") == TEST_ANOTHER_OWNER

    @staticmethod
    def test_get_comment_by_id_with_likes_positive_scenario(prepare_likes, test_app):
        url = reverse(
            "CommentGetOrUpdateView", (prepare_likes.notes[0].id, prepare_likes.comments[0].id)
        )
        response = test_app.get(url)
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert "likes" in response_data
        assert response_data["likes"]["count"] == 2
        assert response_data["likes"]["is_current_user_liked"]

    @staticmethod
    def test_get_comment_by_id_delete_likes_before_retrieve_positive_scenario(
        prepare_likes,
        test_app,
    ):
        test_app.delete(
            reverse(
                "CommentLikesView",
                (
                    prepare_likes.notes[0].id,
                    prepare_likes.comments[0].id,
                ),
            ),
            data=json.dumps({}),
            content_type="application/json",
        )
        response = test_app.get(
            reverse(
                "CommentGetOrUpdateView",
                (
                    POST_UUID_1,
                    prepare_likes.comments[0].id,
                ),
            )
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()

        assert response_data["likes"]["count"] == 1
        assert not response_data["likes"]["is_current_user_liked"]

    @staticmethod
    def test_get_comment_fails_with_wrong_note_id(prepare_comments, test_app):
        wrong_note_id = str(uuid.uuid4())
        url = reverse("CommentGetOrUpdateView", (wrong_note_id, prepare_comments.comments[0].id))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_get_comment_fails_with_wrong_comment_id(prepare_comments, test_app):
        wrong_comment_id = str(uuid.uuid4())
        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, wrong_comment_id))
        response = test_app.get(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_update_own_comment_positive_scenario(prepare_comments, test_app):
        my_comment = [
            _
            for _ in filter(
                lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.notes[0].comments.all()
            )
        ][0]

        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, my_comment.id))
        updated_comment = {"content": "new updated content"}
        response = test_app.put(
            url, data=json.dumps(updated_comment), content_type="application/json"
        )
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data.get("id") == str(my_comment.id)
        assert response_data.get("owner") == my_comment.owner
        assert response_data.get("content") == "new updated content"

        comment_data = Comment.objects.get(id=response_data.get("id"))
        assert comment_data.content == "new updated content"

    @staticmethod
    def test_update_fails_when_someone_else_comment(prepare_comments, test_app):

        alien_comment = prepare_comments.comments[0]
        alien_comment.owner = TEST_ANOTHER_OWNER
        alien_comment.save()

        url = reverse("CommentGetOrUpdateView", (POST_UUID_3, alien_comment.id))
        updated_comment = {"content": "new updated content"}
        response = test_app.put(
            url, data=json.dumps(updated_comment), content_type="application/json"
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

        comment_data = Comment.objects.get(id=alien_comment.id)
        assert comment_data.content != "new updated content"

    @staticmethod
    def test_update_fails_with_wrong_note_id(prepare_comments, test_app):
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]
        wrong_note_id = str(uuid.uuid4())
        url = reverse("CommentGetOrUpdateView", (wrong_note_id, my_comment.id))
        updated_comment = {"content": "new updated content"}
        response = test_app.put(
            url, data=json.dumps(updated_comment), content_type="application/json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_update_fails_with_wrong_comment_id(prepare_comments, test_app):
        wrong_comment_id = str(uuid.uuid4())
        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, wrong_comment_id))
        updated_comment = {"content": "new updated content"}
        response = test_app.put(
            url, data=json.dumps(updated_comment), content_type="application/json"
        )
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def test_delete_own_comment_positive_scenario(prepare_comments, test_app):

        # Only the first comment has replies
        my_comment = prepare_comments.comments[0]
        my_comment.owner = TEST_ORIGIN_OWNER
        my_comment.save()

        replies = list(my_comment.replies.all())

        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, my_comment.id))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert not Comment.objects.filter(id=my_comment.id).exists()
        # check that all replies for specific are removed
        assert not Comment.objects.filter(id=replies[0].id).exists()
        assert not Comment.objects.filter(id=replies[1].id).exists()

    @staticmethod
    def test_delete_own_reply_positive_scenario(prepare_comments, test_app):

        # Only the first comment has replies
        my_comment = prepare_comments.comments[0]
        my_comment.owner = TEST_ORIGIN_OWNER
        my_comment.save()

        my_reply = my_comment.replies.all()[0]
        my_reply.owner = TEST_ORIGIN_OWNER
        my_reply.save()

        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, my_reply.id))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_200_OK
        assert not Comment.objects.filter(id=my_reply.id).exists()

    @staticmethod
    def test_delete_fails_when_someone_else_comment(prepare_comments, test_app):

        alien_comment = prepare_comments.comments[0]
        alien_comment.owner = TEST_ANOTHER_OWNER
        alien_comment.save()

        url = reverse("CommentGetOrUpdateView", (POST_UUID_3, alien_comment.id))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert Comment.objects.filter(id=alien_comment.id).exists()

    @staticmethod
    def test_delete_fails_with_wrong_note_id(prepare_comments, test_app):
        wrong_note_id = str(uuid.uuid4())
        my_comment = [
            _ for _ in filter(lambda c: c.owner == TEST_ORIGIN_OWNER, prepare_comments.comments)
        ][0]

        url = reverse("CommentGetOrUpdateView", (wrong_note_id, my_comment.id))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert Comment.objects.filter(id=my_comment.id).exists()

    @staticmethod
    def test_delete_fails_with_wrong_comment_id(prepare_comments, test_app):
        wrong_comment_id = str(uuid.uuid4())
        url = reverse("CommentGetOrUpdateView", (POST_UUID_1, wrong_comment_id))
        response = test_app.delete(url)
        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert not Comment.objects.filter(id=wrong_comment_id).exists()

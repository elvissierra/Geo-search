from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django import db
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiResponse

from geo_search_api.apps.comments.models import Comment
from geo_search_api.apps.notes.models import Note
from geo_search_api.api.permissions import IsNoteOwner, IsCommentOwner
from geo_search_api.api.notes.serializers import (
    NoteSerializer,
    NoteUpdateSerializer,
    CreateNoteSerializer,
    GetNotesQuerySerializer,
    PaginationQuerySerializer,
)
from geo_search_api.api.notes.paginators import (
    NotesPageNumberPagination,
    CommentsPageNumberPagination,
    LikesPageNumberPagination,
)
from geo_search_api.api.notes.swagger_examples import paginated_notes_example
from geo_search_api.api.likes.serializers import LikesSumUpSerializer, LikeGetSerializer
from geo_search_api.api.likes.swagger_examples import paginated_likes_example
from geo_search_api.api.comments.serializers import (
    CommentGetSerializer,
    CommentCreateSerializer,
    CommentUpdateSerializer,
)
from geo_search_api.api.comments.swagger_examples import paginated_comments_example


class NotesGetOrCreateView(APIView):
    paginator = NotesPageNumberPagination()

    @extend_schema(
        parameters=[PaginationQuerySerializer, GetNotesQuerySerializer],
        responses={
            200: "Ok",
            401: OpenApiResponse(description="Unauthorized"),
        },
        examples=[paginated_notes_example],
    )
    def get(self, request):
        """Retrieve all notes by category."""
        params = GetNotesQuerySerializer(data=request.query_params)
        params.is_valid(raise_exception=True)
        notes = Note.objects.filter(**params.validated_data).all()
        result_page = self.paginator.paginate_queryset(notes, request)
        serializer = NoteSerializer(result_page, many=True, context={"request": request})
        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        request=CreateNoteSerializer,
        responses={
            201: NoteSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
        },
    )
    def post(request):
        """Create new note."""
        request.data["owner"] = request.user["id"]
        serializer = NoteSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteGetOrUpdateView(APIView):
    permission_classes = [IsNoteOwner]

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    @staticmethod
    @extend_schema(
        responses={
            200: NoteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, note_id):
        """Get a specific note by id."""
        note = get_object_or_404(Note, id=note_id)
        return Response(NoteSerializer(note, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        request=NoteUpdateSerializer,
        responses={
            200: NoteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, note_id):
        """Update a specific note by id."""
        note = get_object_or_404(Note, id=note_id)
        serializer = NoteUpdateSerializer(note, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(NoteSerializer(note, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        responses={
            200: NoteSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, note_id):
        """Delete a specific note by id."""
        note = get_object_or_404(Note, id=note_id)
        note.delete()
        return Response(NoteSerializer(note, context={"request": request}).data)


class CommentsGetOrCreateView(APIView):
    paginator = CommentsPageNumberPagination()

    @extend_schema(
        deprecated=True,
        parameters=[PaginationQuerySerializer],
        responses={
            200: "Ok",
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
        examples=[paginated_comments_example],
    )
    def get(self, request, note_id):
        """
        Retrieve all comments and their replies under a post/idea with pagination.

        Note: this endpoint will remove in the next version of API. Use unified `/api/comments` API
        instead.
        """
        comments = Comment.objects.filter(
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
            parent_id=None,
        ).all()
        result_page = self.paginator.paginate_queryset(comments, request)
        serializer = CommentGetSerializer(result_page, many=True, context={"request": request})
        return self.paginator.get_paginated_response(serializer.data)

    @staticmethod
    @extend_schema(
        deprecated=True,
        request=CommentCreateSerializer,
        responses={
            201: CommentGetSerializer,
            400: OpenApiResponse(description="Bad Request"),
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def post(request, note_id):
        """
        Create a comment under a post/idea.

        Note: this endpoint will remove in the next version of API. Use unified `/api/comments` API
        instead.
        """
        request.data["owner"] = request.user["id"]
        request.data["object_id"] = note_id
        request.data["object_type"] = ContentType.objects.get(app_label="notes", model="note").id
        serializer = CommentGetSerializer(data=request.data, context={"request": request})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CommentGetOrUpdateView(APIView):
    permission_classes = [IsCommentOwner]

    def get_permissions(self):
        if self.request.method == "GET":
            return []
        return super().get_permissions()

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            200: CommentGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def get(request, note_id, comment_id):
        """
        Get a specific comment by id.

        Note: this endpoint will remove in the next version of API. Use unified `/api/comments` API
        instead.
        """
        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )
        response_data = CommentGetSerializer(comment, context={"request": request}).data
        return Response(response_data)

    @staticmethod
    @extend_schema(
        deprecated=True,
        request=CommentUpdateSerializer,
        responses={
            200: CommentGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def put(request, note_id, comment_id):
        """
        Update a specific comment or reply by id.

        Note: this endpoint will remove in the next version of API. Use unified `/api/comments` API
        instead.
        """
        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )
        serializer = CommentUpdateSerializer(comment, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response(CommentGetSerializer(comment, context={"request": request}).data)

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            200: CommentGetSerializer,
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Forbidden"),
            404: OpenApiResponse(description="Not Found"),
        },
    )
    def delete(request, note_id, comment_id):
        """
        Delete a specific comment by id.

        Note: this endpoint will remove in the next version of API. Use unified `/api/comments` API
        instead.
        """
        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )
        comment.delete()
        return Response(CommentGetSerializer(comment, context={"request": request}).data)


class NoteLikesView(APIView):
    paginator = LikesPageNumberPagination()

    @extend_schema(
        deprecated=True,
        parameters=[PaginationQuerySerializer],
        responses={
            200: "Ok",
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Returns when the note does not exists"),
        },
        examples=[paginated_likes_example],
    )
    def get(self, request, note_id):
        """
        Retrieve all likes of the post/idea.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        note = get_object_or_404(Note, id=note_id)
        likes = note.likes.all()

        result_page = self.paginator.paginate_queryset(likes, request)
        serializer = LikeGetSerializer(result_page, many=True, context={"request": request})
        return self.paginator.get_paginated_response(
            {
                "results": serializer.data,
                "is_current_user_liked": note.does_the_user_liked(request.user["id"]),
            }
        )

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            201: OpenApiResponse(
                LikesSumUpSerializer, description="Returns when the like is successfully created"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Returns when the user tries to like the note again"),
            404: OpenApiResponse(description="Returns when the note does not exists"),
        },
    )
    def post(request, note_id):
        """
        Create a like for the post/idea.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        note = get_object_or_404(Note, id=note_id)

        try:
            with transaction.atomic():
                note.likes.create(user_id=request.user["id"])
        except db.IntegrityError as exc:
            # If we catch the exception related to unique constraint of `Like` model, handle it and
            # return an appropriate response to the client.
            if "unique_type_id_user" in exc.args[0]:
                return Response(
                    {"detail": "You have already liked this note."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return Response(
            LikesSumUpSerializer(note.get_likes_sum_up(request.user["id"])).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            200: OpenApiResponse(
                LikesSumUpSerializer, description="Returns when the like is successfully deleted"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(description="Returns when the like does not exists for the note"),
            404: OpenApiResponse(description="Returns when the note does not exists"),
        },
    )
    def delete(request, note_id):
        """
        Delete a like from the post/idea.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        note = get_object_or_404(Note, id=note_id)
        like = note.likes.filter(user_id=request.user["id"]).first()

        if like is None:
            return Response(
                {"detail": "Your like does not exist for this note."},
                status=status.HTTP_403_FORBIDDEN,
            )

        note.likes.remove(like)

        return Response(
            LikesSumUpSerializer(note.get_likes_sum_up(request.user["id"])).data,
            status=status.HTTP_200_OK,
        )


class CommentLikesView(APIView):
    paginator = LikesPageNumberPagination()

    @extend_schema(
        deprecated=True,
        parameters=[PaginationQuerySerializer],
        responses={
            200: "Ok",
            401: OpenApiResponse(description="Unauthorized"),
            404: OpenApiResponse(description="Returns when the note does not exists"),
        },
        examples=[paginated_likes_example],
    )
    def get(self, request, note_id, comment_id):
        """
        Retrieve all likes of the comment.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )

        result_page = self.paginator.paginate_queryset(comment.likes.all(), request)
        serializer = LikeGetSerializer(result_page, many=True, context={"request": request})
        return self.paginator.get_paginated_response(
            {
                "results": serializer.data,
                "is_current_user_liked": comment.does_the_user_liked(request.user["id"]),
            }
        )

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            201: OpenApiResponse(
                LikesSumUpSerializer, description="Returns when the like is successfully created"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(
                description="Returns when the user tries to like the comment again"
            ),
            404: OpenApiResponse(description="Returns when a note or a comment does not exists"),
        },
    )
    def post(request, note_id, comment_id):
        """
        Create a like for the comment.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )

        try:
            with transaction.atomic():
                comment.likes.create(user_id=request.user["id"])
        except db.IntegrityError as exc:
            # If we catch the exception related to unique constraint of `Like` model, handle
            # it and return an appropriate response to the client.
            if "unique_type_id_user" in exc.args[0]:
                return Response(
                    {"detail": "You have already liked this comment."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        return Response(
            LikesSumUpSerializer(comment.get_likes_sum_up(request.user["id"])).data,
            status=status.HTTP_201_CREATED,
        )

    @staticmethod
    @extend_schema(
        deprecated=True,
        responses={
            200: OpenApiResponse(
                LikesSumUpSerializer, description="Returns when the like is successfully deleted"
            ),
            401: OpenApiResponse(description="Unauthorized"),
            403: OpenApiResponse(
                description="Returns when the like does not exists for the comment"
            ),
            404: OpenApiResponse(description="Returns when a note or a comment does not exists"),
        },
    )
    def delete(request, note_id, comment_id):
        """
        Delete a like from the comment.

        Note: this endpoint will remove in the next version of API. Use unified `/api/likes` API
        instead.
        """

        comment = get_object_or_404(
            Comment,
            id=comment_id,
            object_type=ContentType.objects.get(app_label="notes", model="note"),
            object_id=note_id,
        )
        like = comment.likes.filter(user_id=request.user["id"]).first()

        if like is None:
            return Response(
                {"detail": "Your like does not exist for this comment."},
                status=status.HTTP_403_FORBIDDEN,
            )

        comment.likes.remove(like)

        return Response(
            LikesSumUpSerializer(comment.get_likes_sum_up(request.user["id"])).data,
            status=status.HTTP_200_OK,
        )

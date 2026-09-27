from rest_framework.permissions import BasePermission
from rest_framework.exceptions import NotFound
from geo_search_api.apps.notes.models import Note, Comment
from geo_search_api.apps.ideas.models import Idea

RESTRICTED_STAGES = ["Evaluation", "Closed"]


class Permission(BasePermission):
    @staticmethod
    def is_authenticated(request):
        """
        Check user is authenticated
        @param request: rest_framework.request.Request
        @return: bool value
        """
        if hasattr(request.user, "is_authenticated"):
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user)


class IsNoteOwner(Permission):
    def has_permission(self, request, view):
        if self.is_authenticated(request):
            note_id = request.parser_context.get("kwargs", {}).get("note_id")
            note_queryset = Note.objects.filter(id=note_id)
            if note_queryset.exists():
                return note_queryset.filter(owner=request.user["id"]).exists()
            raise NotFound
        return False


class IsCommentOwner(Permission):
    def has_permission(self, request, view):
        if self.is_authenticated(request):
            comment_id = request.parser_context.get("kwargs", {}).get("comment_id")
            comment_queryset = Comment.objects.filter(id=comment_id)
            if comment_queryset.exists():
                return comment_queryset.filter(owner=request.user["id"]).exists()
            raise NotFound("The comment does not exists.")
        return False


class IsIdeaOwner(Permission):
    def has_permission(self, request, view):
        if self.is_authenticated(request):
            idea_id = request.parser_context.get("kwargs", {}).get("idea_id")
            idea_queryset = Idea.objects.filter(id=idea_id)
            if idea_queryset.exists():
                return idea_queryset.filter(owner=request.user["id"]).exists()
            raise NotFound
        return False

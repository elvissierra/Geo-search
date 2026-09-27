from django.urls import path

from geo_search_api.api.notes import views

urlpatterns = [
    path("", views.NotesGetOrCreateView.as_view(), name="NotesGetOrCreateView"),
    path("<uuid:note_id>/", views.NoteGetOrUpdateView.as_view(), name="NoteGetOrUpdateView"),
    path(
        "<uuid:note_id>/comments/",
        views.CommentsGetOrCreateView.as_view(),
        name="CommentsGetOrCreateView",
    ),
    path(
        "<uuid:note_id>/comments/<uuid:comment_id>/",
        views.CommentGetOrUpdateView.as_view(),
        name="CommentGetOrUpdateView",
    ),
    path(
        "<uuid:note_id>/likes",
        views.NoteLikesView.as_view(),
        name="NoteLikesView",
    ),
    path(
        "<uuid:note_id>/comments/<uuid:comment_id>/likes",
        views.CommentLikesView.as_view(),
        name="CommentLikesView",
    ),
]

from django.urls import path

from . import views

app_name = "projects"

urlpatterns = [
    path("list/", views.project_list_view, name="list"),
    path("favorites/", views.favorite_projects_view, name="favorites"),
    path("create-project/", views.create_project_view, name="create"),
    path("<int:project_id>/", views.project_details_view, name="details"),
    path("<int:project_id>/edit/", views.edit_project_view, name="edit"),
    path("<int:project_id>/toggle-favorite/", views.toggle_favorite_view, name="toggle_favorite"),
    path("<int:project_id>/toggle-participate/", views.toggle_participate_view, name="toggle_participate"),
    path("<int:project_id>/complete/", views.complete_project_view, name="complete"),
]

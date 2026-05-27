from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Project
from .utils import paginate

PROJECTS_PAGE_SIZE = 12
PROJECT_DETAILS_URL_NAME = "projects:details"
NOT_FOUND_PAYLOAD = {"status": "error", "message": "Project not found"}


def _get_project_or_json_404(project_id):
    project = Project.objects.filter(pk=project_id).first()
    if project is None:
        return None, JsonResponse(NOT_FOUND_PAYLOAD, status=HTTPStatus.NOT_FOUND)
    return project, None


def project_list_view(request):
    queryset = Project.objects.select_related("owner").order_by("-created_at")
    page_obj = paginate(request, queryset, PROJECTS_PAGE_SIZE)
    return render(
        request,
        "projects/project_list.html",
        {
            "projects": page_obj.object_list,
            "page_obj": page_obj,
            "query_prefix": "",
        },
    )


def project_details_view(request, project_id):
    project = get_object_or_404(
        Project.objects.select_related("owner"), pk=project_id
    )
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def favorite_projects_view(request):
    queryset = request.user.favorites.select_related("owner").order_by("-created_at")
    return render(
        request,
        "projects/favorite_projects.html",
        {"projects": queryset},
    )


@login_required
def create_project_view(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.owner = request.user
            project.save()
            project.participants.add(request.user)
            return redirect(PROJECT_DETAILS_URL_NAME, project_id=project.id)
        return render(
            request,
            "projects/create-project.html",
            {"form": form, "is_edit": False},
        )
    return render(
        request,
        "projects/create-project.html",
        {"form": ProjectForm(), "is_edit": False},
    )


@login_required
def edit_project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return HttpResponseForbidden("Доступ запрещён.")
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect(PROJECT_DETAILS_URL_NAME, project_id=project.id)
        return render(
            request,
            "projects/create-project.html",
            {"form": form, "is_edit": True},
        )
    form = ProjectForm(instance=project)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": True},
    )


@require_POST
@login_required
def toggle_favorite_view(request, project_id):
    project, error = _get_project_or_json_404(project_id)
    if error is not None:
        return error
    is_favorite = request.user.favorites.filter(pk=project.pk).exists()
    if is_favorite:
        request.user.favorites.remove(project)
    else:
        request.user.favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": not is_favorite})


@require_POST
@login_required
def toggle_participate_view(request, project_id):
    project, error = _get_project_or_json_404(project_id)
    if error is not None:
        return error
    is_participant = project.participants.filter(pk=request.user.pk).exists()
    if is_participant:
        project.participants.remove(request.user)
    else:
        project.participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_POST
@login_required
def complete_project_view(request, project_id):
    project, error = _get_project_or_json_404(project_id)
    if error is not None:
        return error
    if project.owner_id != request.user.id or project.status != STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=HTTPStatus.BAD_REQUEST)
    project.status = STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": STATUS_CLOSED})

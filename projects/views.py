from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Project

PROJECTS_PAGE_SIZE = 12


def project_list_view(request):
    queryset = Project.objects.all().order_by("-created_at")
    paginator = Paginator(queryset, PROJECTS_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
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
    project = get_object_or_404(Project, pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


@login_required
def favorite_projects_view(request):
    queryset = request.user.favorites.all().order_by("-created_at")
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
            return redirect(f"/projects/{project.id}")
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
            return redirect(f"/projects/{project.id}")
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
    project = get_object_or_404(Project, pk=project_id)
    if project in request.user.favorites.all():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({"status": "ok", "favorited": favorited})


@require_POST
@login_required
def toggle_participate_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user in project.participants.all():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@require_POST
@login_required
def complete_project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id or project.status != STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=400)
    project.status = STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": STATUS_CLOSED})

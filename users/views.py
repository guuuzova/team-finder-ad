from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from projects.models import Project

from .forms import EditProfileForm, LoginForm, PasswordChangeForm, RegisterForm
from .models import User

USERS_PAGE_SIZE = 12
HOME_URL = "/projects/list/"

FILTER_FAVORITE_OWNERS = "owners-of-favorite-projects"
FILTER_PARTICIPATING_OWNERS = "owners-of-participating-projects"
FILTER_INTERESTED_IN_MY = "interested-in-my-projects"
FILTER_PARTICIPANTS_OF_MY = "participants-of-my-projects"
ALLOWED_FILTERS = {
    FILTER_FAVORITE_OWNERS,
    FILTER_PARTICIPATING_OWNERS,
    FILTER_INTERESTED_IN_MY,
    FILTER_PARTICIPANTS_OF_MY,
}


def register_view(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            user = authenticate(
                request, email=user.email, password=form.cleaned_data["password"]
            )
            if user is not None:
                login(request, user)
            return redirect(HOME_URL)
        return render(request, "users/register.html", {"form": form})
    return render(request, "users/register.html", {"form": RegisterForm()})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                email=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect(HOME_URL)
            form.add_error(None, "Неверный имейл или пароль")
        return render(request, "users/login.html", {"form": form})
    return render(request, "users/login.html", {"form": LoginForm()})


def logout_view(request):
    logout(request)
    return redirect(HOME_URL)


def _apply_user_filter(queryset, active_filter, current_user):
    my_projects = Project.objects.filter(owner=current_user)
    if active_filter == FILTER_FAVORITE_OWNERS:
        return queryset.filter(
            owned_projects__in=current_user.favorites.all()
        ).distinct()
    if active_filter == FILTER_PARTICIPATING_OWNERS:
        return queryset.filter(
            owned_projects__in=current_user.participated_projects.all()
        ).distinct()
    if active_filter == FILTER_INTERESTED_IN_MY:
        return queryset.filter(favorites__in=my_projects).distinct()
    if active_filter == FILTER_PARTICIPANTS_OF_MY:
        return queryset.filter(participated_projects__in=my_projects).distinct()
    return queryset.none()


def user_list_view(request):
    queryset = User.objects.all().order_by("id")
    active_filter = request.GET.get("filter")
    if request.user.is_authenticated and active_filter in ALLOWED_FILTERS:
        queryset = _apply_user_filter(queryset, active_filter, request.user)
    else:
        active_filter = None

    paginator = Paginator(queryset, USERS_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))
    query_prefix = f"filter={active_filter}&" if active_filter else ""
    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj.object_list,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": query_prefix,
        },
    )


def user_details_view(request, user_id):
    profile_user = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": profile_user})


@login_required
def edit_profile_view(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(f"/users/{request.user.id}")
        return render(request, "users/edit_profile.html", {"form": form})
    form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password_view(request):
    if request.method == "POST":
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            return redirect(f"/users/{request.user.id}")
        return render(request, "users/change_password.html", {"form": form})
    form = PasswordChangeForm(request.user)
    return render(request, "users/change_password.html", {"form": form})

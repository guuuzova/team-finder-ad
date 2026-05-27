from django.core.paginator import Paginator


def paginate(request, queryset, page_size):
    paginator = Paginator(queryset, page_size)
    return paginator.get_page(request.GET.get("page"))

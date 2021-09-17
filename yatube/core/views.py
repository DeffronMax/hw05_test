from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def permission_denied(request, exception):
    template = 'core/403.html'
    return render(request, template, status=403)


def csrf_failure(request, reason=''):
    template = 'core/403csrf.html'
    return render(request, template)


def server_error(request, *args, **argv):
    return render(request, 'core/500.html', {'path': request.path}, status=500)

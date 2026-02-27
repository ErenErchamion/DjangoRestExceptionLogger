from django.http import HttpResponse
from django.urls import path


def ok_view(request):
    return HttpResponse("ok")


urlpatterns = [
    path("", ok_view, name="ok"),
]


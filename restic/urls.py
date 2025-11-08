from django.urls import path
from .apps import ResticConfig
from .views import RestHomeView, RestAboutView

app_name = ResticConfig.name

urlpatterns = [
    path("", RestHomeView.as_view(), name="index"),
    path("about/", RestAboutView.as_view(), name="about"),
]

from django.conf.urls.static import static
from django.urls import path

from config import settings
from .apps import ResticConfig
from .views import RestHomeView, RestAboutView, TestAboutView, RestBookingView, BookingDetailView

app_name = ResticConfig.name

urlpatterns = [
    path("", RestHomeView.as_view(), name="index"),
    path("about/", RestAboutView.as_view(), name="about"),
    path('booking/', RestBookingView.as_view(), name='booking'),
    path('booking/<int:pk>/', BookingDetailView.as_view(), name='booking_detail'),
    path("test/", TestAboutView.as_view(), name="test"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
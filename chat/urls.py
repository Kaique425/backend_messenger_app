from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

api_router = SimpleRouter()

api_router.register("sectors", views.SectorViewSet)

print(api_router.urls)

urlpatterns = [
    path("webhook", views.Webhook.as_view(), name="webhook"),
    path("messages", views.send_message, name="send_message"),
    path("messages/midia", views.MidiaUpload.as_view(), name="midia_upload"),
    path("hsms", views.hsm_view, name="hsm"),
    path("messages/hsm", views.send_hsm_messages, name="send_hsm"),
    path(
        "attendances",
        views.AttendanceListAPIView.as_view(),
        name="get_messages",
    ),
    path(
        "attendances/history/<int:id>",
        views.HistoryMessageListAPIView.as_view(),
        name="history",
    ),
    path(
        "attendances/<int:pk>",
        views.AttendanceDetailAPIView.as_view(),
        name="attendance_detail",
    ),
    path("channels", views.ChannelsViewSet.as_view(), name="waba_channels"),
    path("", include(api_router.urls)),
]

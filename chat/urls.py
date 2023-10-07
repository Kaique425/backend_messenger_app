from django.urls import path

from . import views

urlpatterns = [
    path("", views.lobby, name="lobby"),
    path("webhook", views.webhook, name="webhook"),
    path("messages", views.send_message, name="send_message"),
    path("messages/midia", views.MidiaUpload.as_view(), name="midia_upload"),
    path("hsms", views.hsm_view, name="hsm"),
    path("messages/hsm", views.send_hsm_messages, name="send_hsm"),
    path(
        "sectors",
        views.SectorViewSet.as_view({"get": "list", "post": "create"}),
        name="sectors_view",
    ),
    path(
        "sectors/<int:pk>",
        views.SectorViewSet.as_view(
            {
                "get": "retrieve",
                "patch": "partial_update",
                "delete": "destroy",
            }
        ),
        name="sectors_view",
    ),
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
]

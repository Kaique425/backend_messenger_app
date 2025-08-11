from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

api_router = SimpleRouter()

api_router.register("sectors", views.SectorViewSet)
api_router.register("attendances", views.AttendanceDetailAPIView)
api_router.register("contacts", views.ContactViewSet)
api_router.register("events", views.WhatsAppPOSTViewSet)

print(api_router.urls)

urlpatterns = [
    path("webhook", views.Webhook.as_view(), name="webhook"),
    path("messages", views.SendMessageAPIView.as_view(), name="send_message"),
    path("messages/midia", views.MidiaUploadAPIView.as_view(), name="midia_upload"),
    path("hsms", views.HsmAPIView.as_view(), name="hsm"),
    path("messages/hsm", views.SendHsmMessageAPIView.as_view(), name="send_hsm"),
    path("contacts/import", views.BatchContactImport.as_view(), name="contact-import"),
    path(
        "attendances/history/<int:id>",
        views.HistoryMessageListAPIView.as_view(),
        name="history",
    ),
    path("channels", views.ChannelsViewSet.as_view(), name="waba_channels"),
    path("", include(api_router.urls)),
]

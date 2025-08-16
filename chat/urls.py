from django.urls import include, path
from rest_framework.routers import SimpleRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

api_router = SimpleRouter()

api_router.register("sectors", views.SectorViewSet)
api_router.register("attendances", views.AttendanceDetailAPIView)
api_router.register("contacts", views.ContactViewSet)
api_router.register("events", views.WhatsAppPOSTViewSet)
api_router.register("channels", views.ChannelsViewSet)


urlpatterns = [
    path("webhook", views.Webhook.as_view(), name="webhook"),
    path("me", views.MeAPIView.as_view()),
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
    path("api/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("", include(api_router.urls)),
]

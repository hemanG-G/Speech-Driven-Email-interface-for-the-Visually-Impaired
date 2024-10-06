from django.urls import path
from .views import HomeView,TrashView,SentView,NewMailView,ReadMailView,DownloadAttachment,HandleRecognizedSpeech,HandleAjaxSubmit
from django.conf.urls import url

app_name = "EmailApp"

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('trash/', TrashView.as_view(), name="trash"),
    path('sent/', SentView.as_view(), name="sentmails"),
    path('messages/<str:messageid>/', ReadMailView.as_view(), name="readmail"),
    path('new/', NewMailView.as_view(), name="newmessage"),
    path('downloadattachment/<str:messageId>/', DownloadAttachment.as_view(), name="download"),
    url(r'^ajax/recognized/$',HandleRecognizedSpeech.as_view(),name="handlerecognition"),
    url(r'^ajax/submit/$',HandleAjaxSubmit.as_view(),name="handleAjaxSubmit"),
]
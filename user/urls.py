from django.urls import path
from . import views


app_name = 'user'

urlpatterns = [
    path('start/', views.StartAuthentication.as_view(), name='start-authentication'),
]

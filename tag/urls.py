from django.urls import path
from . import views


app_name = 'tag'

urlpatterns = [
    path('', views.TagView.as_view(), name='tag-endpoints')
]

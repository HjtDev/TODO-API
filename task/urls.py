from django.urls import path
from . import views


app_name = 'task'

urlpatterns = [
    path('', views.TaskView.as_view(), name='task-endpoints'),
]
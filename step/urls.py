from django.urls import path
from . import views


app_name = 'step'

urlpatterns = [
    path('', views.StepView.as_view(), name='step-endpoints'),
]
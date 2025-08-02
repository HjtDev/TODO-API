from django.urls import path
from . import views


app_name = 'user'

urlpatterns = [
    path('start/', views.StartAuthentication.as_view(), name='start-authentication'),
    path('complete/', views.CompleteAuthentication.as_view(), name='complete-authentication'),
    path('renew/', views.RenewToken.as_view(), name='renew-token'),
    path('edit/', views.EditProfile.as_view(), name='edit-profile'),
]

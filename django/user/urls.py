from django.urls import path, include

from django.contrib.auth.views import (
    LoginView,
    LogoutView,
)
from user.views import RegisterView

app_name = 'user'
urlpatterns = [
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(), name='logout'),
    # path('', include('django.contrib.auth.urls')),
    path('register', RegisterView.as_view(), name='register'),
]

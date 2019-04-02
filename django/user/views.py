from django.contrib.auth.forms import UserCreationForm
from django.views.generic.edit import CreateView
from django.urls import reverse

class RegisterView(CreateView):
    template_name = 'user/register.html'
    form_class = UserCreationForm
    success_url = 'login'
    
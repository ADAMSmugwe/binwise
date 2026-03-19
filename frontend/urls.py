from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='home'),  # homepage serves index.html
]
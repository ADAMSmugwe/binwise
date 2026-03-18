from django.urls import path
from . import views

urlpatterns = [
    path('classify', views.classify, name='classify'),
    path('health', views.health, name='health'),
]

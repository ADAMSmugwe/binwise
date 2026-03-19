from django.urls import path
from . import views

urlpatterns = [
    path('classify/', views.WasteClassificationView.as_view(), name='classify'),
    path('health/', views.health, name='health'),
]

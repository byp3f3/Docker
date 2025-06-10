from django.urls import path, include
from .views import *

urlpatterns = [
    path('', info_view, name='info_view'),
]

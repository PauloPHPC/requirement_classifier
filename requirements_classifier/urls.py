from django.urls import path
from .views import index, process_pdf

urlpatterns = [
    path('', index, name='index'),
    path('process_pdf/', process_pdf, name='process_pdf'),
    ]
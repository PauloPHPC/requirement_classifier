from django.urls import path
from .views import index, process_pdf, save_requirements

urlpatterns = [
    path('', index, name='index'),
    path('process_pdf/', process_pdf, name='process_pdf'),
    path('save_requirements/', save_requirements, name='save_requirements')
    ]
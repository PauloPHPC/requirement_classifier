from django.urls import path
from .views import index, process_pdf, save_requirements, export_csv, classify_manual_requirement

urlpatterns = [
    path('', index, name='index'),
    path('process_pdf/', process_pdf, name='process_pdf'),
    path('save_requirements/', save_requirements, name='save_requirements'),
    path('export_csv/', export_csv, name='export_csv'),
    path('classify_manual_requirement/', classify_manual_requirement, name='classify_manual_requirement'),
    ]
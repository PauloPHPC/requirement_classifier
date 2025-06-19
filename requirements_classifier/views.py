import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.conf import settings
from pathlib import Path
from .services.requirements_classifier import RequirementsClassifier
from .services.pdf_utils import PDFUtils

REQ_CLASSIFIER = RequirementsClassifier(
    phi4_model_path="microsoft/phi-4-mini-instruct",
    multitask_model_name="distilbert-base-uncased",
    multitask_bin_path=str(settings.BASE_DIR / "requirements_classifier" / "distilbert" / "multitask_distilbert.bin"),
    multitask_tokenizer_path=str(settings.BASE_DIR / "requirements_classifier" / "distilbert")
)

PDF_HELPER = PDFUtils()

def index(request):
    return render(request, "index.html")

@csrf_exempt
def process_pdf(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"})
    
    pdf_file = request.FILES.get("pdf_file")
    if not pdf_file:
        return JsonResponse({"error": "No PDF file provided"})
    
    pdf_path = PDF_HELPER.save_pdf(pdf_file)
    final_results = REQ_CLASSIFIER.process_pdf(pdf_path)

    return JsonResponse({
        "results": final_results,
        "pdf_path": pdf_path
    }, content_type="application/json")

    



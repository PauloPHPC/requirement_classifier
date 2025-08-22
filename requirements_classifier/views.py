import csv, io, datetime, json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.conf import settings
from pathlib import Path
from .services.requirements_classifier import RequirementsClassifier
from .services.pdf_services import PDFUtils
from .services.db_services import save_requirements_to_db

CSV_FIELDS = [
    "text",
    "classification_ai",
    "confidence_ai",
    "classification_user",
]

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

@csrf_exempt
def save_requirements(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request Method"}, status=400)
    
    data = json.loads(request.body)
    pdf_path = data.get("pdf_path")
    requirements = data.get("requirements")

    if not pdf_path or not requirements:
        return JsonResponse({"error": "Missing PDF path or requirements"}, status=400)
    
    save_requirements_to_db(requirements)

    grouped_by_page = PDF_HELPER.group_requirements_by_page(requirements)
    highlighted_url = PDF_HELPER.highligh_pdf(pdf_path, grouped_by_page)

    return JsonResponse({
        "message": "Requirements saved successfully",
        "highlighted_pdf_url": highlighted_url
    })

@csrf_exempt
def export_csv(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method"}, status=400)
    
    try:
        payload = json.loads(request.body.decode('utf-8'))
        reqs = payload.get("requirements", [])
        base_filename = (payload.get("filename") or "requirements").replace('"', '')

        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for req in reqs:
            writer.writerow({k: req.get(k, "") for k in CSV_FIELDS})

        data = ("\ufeff" + buf.getvalue()).encode('utf-8')
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        resp = HttpResponse(data, content_type='text/csv')
        resp['Content-Disposition'] = f'attachment; filename="{base_filename}_{ts}.csv"'
        return resp
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
    
@csrf_exempt
def classify_manual_requirement(request):
    try:
        data = json.loads(request.body)
        sentence = data.get("text")
        pdf_path = data.get("pdfPath")

        if not sentence:
            return JsonResponse({"error":"Missing requirement text"}, status = 400)
        if not pdf_path:
            return JsonResponse({"error": "Missing PDF path."}, status = 400)
        
        result = REQ_CLASSIFIER.process_manual_requirement(sentence, pdf_path)
        return JsonResponse(result)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

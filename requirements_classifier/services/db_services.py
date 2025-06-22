from ..models import Requirements, Documents

def save_requirements_to_db(requirements):
    
    for requirement in requirements:
        document, _ = Documents.objects.get_or_create(document_name=requirement["project"])

        Requirements.objects.create(
            text = requirement["text"],
            classification_ai = requirement["classification_ai"],
            confidence_ai = requirement["confidence_ai"],
            classification_user = requirement["classification_user"] if requirement["classification_user"] != "---" else "",
            original_text = requirement["original_text"],
            match_score = requirement["match_score"],
            page = requirement["page"],

            project = document
        )
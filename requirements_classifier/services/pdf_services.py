import PyPDF2
import fitz
import random
import os 
import uuid
import tempfile
from django.conf import settings

class PDFUtils:
    """
    A utility class for handling PDF files.
    """

    def __init__(self):
        self.pre_defined_colors = [
            ((255/255), (153/255), (153/255)),  # Red
            ((255/255), (204/255), (153/255)),  # Orange
            ((255/255), (255/255), (153/255)),  # Yellow
            ((153/255), (255/255), (153/255)),  # Green
            ((153/255), (204/255), (255/255)),  # Blue
            ((204/255), (153/255), (255/255)),  # Purple
            ((255/255), (153/255), (204/255)),  # Pink
        ]

    def save_pdf(self, uploaded_file):
        """
        Saves the uploaded PDF as a temporary file.
        Returns the path of the temporary file
        """
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            for chunk in uploaded_file.chunks():
                tmp_file.write(chunk)
            tmp_pdf_path = tmp_file.name

            return tmp_pdf_path

    def extract_text(self, pdf_path):
        """
        Extracts the texts from each page of the PDF and returns a list of Strings.
        """

        texts = []
        with open(pdf_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                texts.append(text)

        return texts
    
    def highligh_pdf(self, input_pdf_path, requirements_by_page):
        """
        Highlights the specified texts in the PDF and saves it to a new file.
        """
        doc = fitz.open(input_pdf_path)
        color_by_text = {}
        text_to_requirement = {}
        requirement_counter = 1

        for page_number, requirements in requirements_by_page.items():
            for requirement in requirements:
                text = requirement.get("original_text", "").strip()
                if not text:
                    continue

                key = (page_number, text)
                if key not in text_to_requirement:
                    text_to_requirement[key] = []
                text_to_requirement[key].append((requirement_counter, requirement))
                requirement_counter += 1
        
        for (page_number, text), requirement_list in text_to_requirement.items():
            if page_number > len(doc):
                continue
            page = doc[page_number - 1]
            text_instances = page.search_for(text)
            if not text_instances:
                continue

            if text not in color_by_text:
                color_by_text[text] = random.choice(self.pre_defined_colors)
            color = color_by_text[text]

            requirement_numbers = [str(num) for num, _ in requirement_list]
            note = f"Requirements: {','.join(requirement_numbers)}"

            for text_instance in text_instances:
                annot = page.add_rect_annot(text_instance)
                annot.set_colors(stroke=color, fill=color)
                annot.set_opacity(0.4)
                annot.set_info({"title": "Requirement", "content": note})
                annot.update()

        self.append_summary_page(doc, requirements_by_page, color_by_text)
        
    
        dest_path = os.path.join(settings.MEDIA_ROOT, "highlighted", f"highlighted_{uuid.uuid4().hex}.pdf")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        doc.save(dest_path)
        doc.close()

        # Retornar URL relativa
        highlighted_url = settings.MEDIA_URL + "highlighted/" + os.path.basename(dest_path)
        return highlighted_url

    
    def group_requirements_by_page(self, requirements):
        """
        Groups the requirements by page
        """
        grouped = {}
        for requirement in requirements:
            if requirement["classification_user"].strip().lower() == "out of scope":
                continue
            page_number = requirement.get("page", 1)
            grouped.setdefault(page_number, []).append(requirement)
        return grouped

        # doc = fitz.open(input_pdf_path)
        # color_by_text = {}
        # text_to_reqs = {} 
        # req_counter = 1
        # print(requirements_by_page)
        # for page_num, requirements in requirements_by_page.items():
        #     for req in requirements:
        #         text = req.get("original_text", "").strip()
        #         if not text:
        #             continue

        #         key = (page_num, text)
        #         if key not in text_to_reqs:
        #             text_to_reqs[key] = []
        #         text_to_reqs[key].append((req_counter, req))
        #         req_counter += 1

        # for (page_num, text), req_list in text_to_reqs.items():
        #     if page_num > len(doc):
        #         continue
        #     page = doc[page_num-1]
        #     text_instaces = page.search_for(text)
        #     if not text_instaces:
        #         continue

        #     if text not in color_by_text:
        #         color_by_text[text] = random.choice(self.pre_defined_colors)
        #     color = color_by_text[text]

        #     req_nums = [str(num) for num, _ in req_list]
        #     note = f"Requirements: {', '.join(req_nums)}"

        #     for text_instance in text_instaces:
        #         annot = page.add_rect_annot(text_instance)
        #         annot.set_colors(stroke=color, fill=color)
        #         annot.set_opacity(0.4)
        #         annot.set_info({"title": "Requirement", "content": note})
        #         annot.update()

        # page_based_grouping = {}
        # for (page_num, _), req_list in text_to_reqs.items():
        #     page_key = f"page_{page_num + 1}"
        #     if page_key not in page_based_grouping:
        #         page_based_grouping[page_key] = []
        #     for _, req in req_list:
        #         page_based_grouping[page_key].append(req)

        # self.append_summary_page(doc, requirements_by_page, color_by_text)
        # doc.save(output_pdf_path)
        # doc.close()
    
    def append_summary_page(self, doc, requirements_by_page, color_by_text):
        """
        Appends a summary page to the PDF with the highlighted texts and their colors.
        """
        summary_rows = []
        count = 1

        for page_num, requirements in requirements_by_page.items():
            for requirement in requirements:
                text = requirement.get("text") or "???"
                original_text = requirement.get("original_text") or "???"
                classification = requirement["classification_user"] if requirement["classification_user"] != "---" else requirement["classification_ai"]
                confidence = requirement["confidence_ai"] if requirement["classification_user"] == "---" else 1.0
                classified_by = "User" if requirement["classification_user"] != "---" else "AI"
                color = color_by_text.get(original_text, (0,0,0))

                summary_rows.append({
                    "count": count,
                    "text": text,
                    "classification": classification,
                    "confidence": confidence,
                    "page": page_num,
                    "classified_by": classified_by,
                    "color": color
                })

                count += 1

        summary_page = doc.new_page(-1)
        summary_page.insert_text((50, 50), "GENERATED REQUIREMENTS", fontsize=16, fontname="helv", fill=(0, 0, 0))

        y = 80
        page_width = 500    

        for row in summary_rows:
            summary_page.insert_text((50, y), f"Requirement #{row['count']} | Type: {row['classification']}", fontsize=12, fontname="helv", fill=(0, 0, 0))
            y += 20
            
            text_height = 12  # fonte 10px ~= 12px altura por linha
            max_line_length = 100
            lines = len(row['text']) // max_line_length + 1
            rect_height = lines * text_height + 10  # padding

            rect = fitz.Rect(50, y, 50 + page_width, y + rect_height)

            summary_page.insert_textbox(rect, f"{row['text']}", fontsize=10, fontname="helv", fill=(0, 0, 0), align=fitz.TEXT_ALIGN_LEFT)
            y += rect_height + 20
            summary_page.insert_text((50, y), f"Page: {row['page']} | Confidence: {round((row['confidence']*100), 4)}%", fontsize=10, fontname="helv", fill=(0, 0, 0))
            y += 20
            summary_page.insert_text((50, y), f"Classified by: {row['classified_by']}", fontsize=8, fontname="helv", fill=(0, 0, 0))
            
            y += 30
            if y > 700:
                summary_page = doc.new_page(-1)
                y = 50
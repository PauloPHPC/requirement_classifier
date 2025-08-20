import PyPDF2
import fitz
import random
import os 
import uuid
import tempfile
import re
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

        doc = fitz.open(pdf_path)
        texts = []
        for page in doc:
            raw_text = page.get_text()
            clean_text = self.clean_page_text(raw_text)
            texts.append(clean_text)
        return texts
    
    def clean_page_text(self, text):
        lines = text.splitlines()
        merged = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                merged.append("")
                continue

            if i + 1 < len(lines) and not re.match(r".*[\.\:\!\?]\s*$", line):
                next_line = lines[i+1].strip()
                line += " " + next_line
                lines[i+1] = ""
            merged.append(line)

        cleaned = []
        last_blank = False
        for line in merged:
            if line == "":
                if not last_blank:
                    cleaned.append(line)
                last_blank = True
            else:
                cleaned.append(line)
                last_blank = False

        return "\n".join(cleaned)
    
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
        Gera páginas com word-wrap e quebra de página automática.
        """
        # Coletar linhas de conteúdo
        rows = []
        count = 1
        for page_num, requirements in requirements_by_page.items():
            for requirement in requirements:
                text = requirement.get("text") or requirement.get("original_text") or "???"
                classification = requirement["classification_user"] if requirement["classification_user"] != "---" else requirement.get("classification_ai", "N/A")
                confidence = requirement["confidence_ai"] if requirement["classification_user"] == "---" else 1.0
                classified_by = "User" if requirement["classification_user"] != "---" else "AI"
                rows.append({
                    "count": count,
                    "text": text,
                    "classification": classification,
                    "confidence": confidence,
                    "page": page_num,
                    "classified_by": classified_by,
                })
                count += 1

        # Layout
        margin_left = 50
        margin_right = 50
        margin_top = 60
        margin_bottom = 50
        title_fs = 16
        head_fs = 12
        body_fs = 10
        lead = 1.35  # line height factor

        # Nova página + cabeçalho
        def new_page():
            p = doc.new_page(-1)
            p.insert_text((margin_left, margin_top - 10), "GENERATED REQUIREMENTS", fontsize=title_fs, fontname="Times-Roman")
            return p, margin_top + 20  # y inicial após o título

        page, y = new_page()
        page_w, page_h = page.rect.width, page.rect.height
        text_w = page_w - margin_left - margin_right
        line_h_body = body_fs * lead
        line_h_head = head_fs * lead

        # footer opcional com número da página
        def add_footer(p):
            try:
                idx = p.number + 1
            except Exception:
                idx = len(doc)
            footer_y = page_h - 25
            p.insert_text((page_w/2 - 10, footer_y), f"{idx}", fontsize=9, fontname="Times-Roman")

        for row in rows:
            # Bloco: cabeçalho
            header = f"Requirement #{row['count']} | Type: {row['classification']}"
            # Quebra de página se necessário (espaço para header + 2 linhas mínimas de corpo)
            min_block = int(line_h_head + 2*line_h_body + 20)
            if y + min_block > page_h - margin_bottom:
                add_footer(page)
                page, y = new_page()

            page.insert_text((margin_left, y), header, fontsize=head_fs, fontname="Times-Roman")
            y += line_h_head

            # Corpo (parágrafo com wrap)
            body = row["text"]
            lines = self._wrap_lines(page, body, text_w, fontsize=body_fs, fontname="Times-Roman")
            for ln in lines:
                if y + line_h_body > page_h - margin_bottom:
                    add_footer(page)
                    page, y = new_page()
                page.insert_text((margin_left, y), ln, fontsize=body_fs, fontname="Times-Roman")
                y += line_h_body

            # Metadados
            meta = f"Page: {row['page']} | Confidence: {round(row['confidence']*100, 2)}% | Classified by: {row['classified_by']}"
            if y + line_h_body > page_h - margin_bottom:
                add_footer(page)
                page, y = new_page()
            page.insert_text((margin_left, y), meta, fontsize=10, fontname="Times-Roman")
            y += line_h_body + 10  # espaçamento entre blocos

        add_footer(page)


    def _page_size(self, doc):
    # Usa a última página para obter tamanho; se não houver, cria uma temporária
        if len(doc) > 0:
            p = doc[-1]
            return p.rect.width, p.rect.height
        else:
            p = doc.new_page(-1)
            w, h = p.rect.width, p.rect.height
            doc.delete_page(-1)
            return w, h

    def _wrap_lines(self, page, text, max_width, fontsize=10, fontname="Times-Roman"):
        """
        Quebra 'text' em linhas que caibam em 'max_width' medindo cada tentativa.
        Retorna lista de strings (linhas).
        """
        words = text.split()
        lines, cur = [], ""
        for w in words:
            test = (cur + " " + w).strip()
            if self._text_width(page, test, fontsize=fontsize, fontname=fontname) <= max_width:
                cur = test
            else:
                if cur:
                    lines.append(cur)
                cur = w
        if cur:
            lines.append(cur)
        # preserva linhas em branco (parágrafos) se houver
        out = []
        for para in text.split("\n"):
            if not para.strip():
                out.append("")  # linha em branco
            else:
                # re-wrap para cada parágrafo
                words = para.split()
                cur = ""
                for w in words:
                    test = (cur + " " + w).strip()
                    if self._text_width(page, test, fontsize=fontsize, fontname=fontname) <= max_width:
                        cur = test
                    else:
                        if cur:
                            out.append(cur)
                        cur = w
                if cur:
                    out.append(cur)
        return [ln for ln in out]

    def _text_width(self, page, s, fontsize=10, fontname="Times-Roman"):
        """
        Mede a largura do texto compatível com várias versões do PyMuPDF
        e com fallback de fonte (Times-Roman) e aproximação final.
        """
        # 1) tenta medir com a fonte pedida
        try:
            return page.get_text_length(s, fontsize=fontsize, fontname=fontname)
        except Exception:
            pass
        try:
            return fitz.get_text_length(s, fontsize=fontsize, fontname=fontname)
        except Exception:
            pass

        # 2) fallback de fonte garantida
        try:
            return page.get_text_length(s, fontsize=fontsize, fontname="Times-Roman")
        except Exception:
            pass
        try:
            return fitz.get_text_length(s, fontsize=fontsize, fontname="Times-Roman")
        except Exception:
            pass

        # 3) última linha de defesa: aproximação monoespaçada
        return len(s) * fontsize * 0.5

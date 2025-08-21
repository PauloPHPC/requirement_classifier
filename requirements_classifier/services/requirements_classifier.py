import torch
import re
import nltk
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from .pdf_services import PDFUtils
from requirements_classifier.ai.networks import load_phi4_model, load_multitask_classifier, generate_requirements
import requests
import re
from config.settings import BASE_DIR

# Definir dispositivo para GPU
device = "cuda" if torch.cuda.is_available() else "cpu"

####
# Label IA
###

# Mapeamento do classifier Binario (F x NF)
labelMap = {
    "LABEL_0":"Funcional",
    "LABEL_1":"NF"
}

# Mapeamento do classifier multi-classes NF
nfLabelMap = {
    "LABEL_0": "NF - Performance",
    "LABEL_1": "NF - Look and Feel",
    "LABEL_2": "NF - Usability",
    "LABEL_3": "NS - Security",
    "LABEL_4": "NF - Availability",
    "LABEL_5": "NF - Scalability",
    "LABEL_6": "NF - Portability",
    "LABEL_7": "NF - Fault Tolerance",
    "LABEL_8": "NF - Operacional",
    "LABEL_9": "NF - Legal",
    "LABEL_10": "NF - Maintenability"
}

class RequirementsClassifier:
    """
    Class that:
    - Extract texts from PDF.
    - Generate requirements based on PDF file (Using phi-4-mini-instruct from Microsoft).
    - Classify between the binary classes Functional x Non Functional using a pretrained BERT.
    - Classify between the multiclasses of Non Functional using a pretrained BERT.
    - Primary function: process_pdf.
    """

    def __init__(self, 
                 phi4_model_path, 
                 multitask_model_name, 
                 multitask_bin_path, 
                 multitask_tokenizer_path
                 ):
        
        self.phi4_pipeline = load_phi4_model(phi4_model_path)
        self.multitask_tokenizer, self.multitask_model = load_multitask_classifier(
            model_name=multitask_model_name,
            bin_path=multitask_bin_path,
            tokenizer_path=multitask_tokenizer_path
        )

        self.pdf_utils = PDFUtils()
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        
        nltk.download("punkt")

        # env = environ.Env()

        # environ.Env.read_env(BASE_DIR / '.env')

        # self.serpapi_key = env("APIKEY")
        
        self.user_prompt = """
        Extract information and generate user software requirements explicitly from the document.  
        The user is a person who benefits from the system being developed.

        Follow these steps strictly:

        1. Identify potential software requirements from the text.
        2. Identify the user who benefits from that requirement.
        3. Identify the objective of that requirement.
        4. Gather explicitly from the text the reason for that requirement.
        5. Structure the requirement exactly as: “As a <user>, I want to <objective> for <reason>”.
        6. Ensure each requirement is concise, clearly described and no longer than two sentences.

        Always ignore technical aspects of the system.  
        End each requirement only with a dot.
        """

        self.system_prompt = """
        Extract information and generate system software requirements explicitly from the document.
        The system is a set of interacting components that work together to achieve a specific goal or fulfill a defined purpose.

        Follow these steps strictly:

        1. Identify potential software requirements from the text.
        2. Identify the type of system or entity.
        3. Classify clearly if the feature is mandatory ("shall") or desirable ("must").
        4. Briefly describe the technical feature explicitly mentioned in the text.
        5. Structure the requirement exactly as: “The <system/entity> shall/must <feature> <description>”.
        6. Ensure each requirement is concise, clearly described and no longer than two sentences.
        
        All requirements must explicitly include technical aspects.  
        End each requirement only with a dot.
        """

    def search_web(self, text, k=3):
        url = "https://serpapi.com/search"
        params = {
            "q":text,
            "api_key": self.serpapi_key,
            "engine": "google",
            "num": k
        }
        response = requests.get(url,params=params)
        data = response.json()
        snippets = []
        for item in data.get("organic_results", []):
            if "snippet" in item:
                snippets.append(item["snippet"])
                if len(snippets) >= k:
                    break
        
        return snippets
    
    # def process_sentence(self, sentence, embeddings_sentence, sentences_pages):
    #     encodings = self.multitask_tokenizer([sentence], truncation=True, padding=True, max_length=256, return_tensors="pt")
    #     input_ids = encodings["input_ids"].to(device)
    #     attention_mask = encodings["attention_mask"].to(device)

    #     with torch.no_grad():
    #         out = self.multitask_model(input_ids=input_ids, attention_mask=attention_mask)

    #     logits_bin = out["logits_bin"].softmax(dim=1)[0]
    #     logits_cat = out["logits_cat"].softmax(dim=1)[0]

    #     label_bin_idx = logits_bin.argmax().item()
    #     type_req = labelMap.get(f"LABEL_{label_bin_idx}", "Unknown")
    #     confidence = round(logits_bin[label_bin_idx].item(), 4)

    #     req_embedding = self.embedding_model.encode(sentence, convert_to_tensor=True)
    #     cos_similar = util.pytorch_cos_sim(req_embedding, embeddings_sentence)[0]
    #     idx_most_similar = cos_similar.argmax().item()

    #     original_text = sentences_pages[idx_most_similar]
    #     match_score = round(float(cos_similar[idx_most_similar]), 4)

    #     result = {
    #         "requirement": sentence,
    #         "confidence": confidence,
    #         "type": type_req,
    #         "original_text": original_text,
    #         "match_score": match_score
    #     }

    #     if type_req == "NF":
    #         label_cat_idx = logits_cat.argmax().item()
    #         nf_type = nfLabelMap.get(f"LABEL_{label_cat_idx}", "Unknown")
    #         result["type"] = nf_type
    #         result["confidence"] = round(logits_cat[label_cat_idx].item(), 4)
        
    #     return result
    
    # def process_page(self, page_content, page_number):
    #     # web_context = self.search_web(page_content + "User software requirements as user story examples", k=5)
    #     # extra_context = "\n".join([f"- {c}" for c in web_context])

    #     # web_context_sys = self.search_web(page_content + "System software requirements examples", k=5)
    #     # extra_context_sys = "\n".join([f"- {c}" for c in web_context_sys])
        

    #     # user_prompt_context = f"""{self.user_prompt} do not repeat user requirements. here are some examples to guide you: {extra_context}"""
    #     # system_prompt_context = f"""{self.system_prompt} do not repeat system requirements. here are some examples to guide you: {extra_context_sys}"""

    #     user_req_text = generate_requirements(self.phi4_pipeline, page_content, self.user_prompt)
    #     system_req_text = generate_requirements(self.phi4_pipeline, page_content, self.system_prompt)

    #     punkt_param = PunktParameters()
    #     sentence_splitter = PunktSentenceTokenizer(punkt_param)
    #     sentences_pages = sentence_splitter.tokenize(page_content)
    #     sentences_pages = [s.strip() for s in sentences_pages if s.strip()]
    #     embeddings_sentences = self.embedding_model.encode(sentences_pages, convert_to_tensor=True)

    #     all_requirements = []

    #     for req_text in [user_req_text, system_req_text]:
    #         sentences = re.split(r"\.\s*", req_text)
    #         sentences = [s.strip() for s in sentences if s.strip()]
    #         for sentence in sentences:
    #             if not re.match(r"^(As a|The )", sentence.strip(), re.IGNORECASE):
    #                 continue

    #             req_result = self.process_sentence(
    #                 sentence,
    #                 embeddings_sentences,
    #                 sentences_pages
    #             )
    #             req_result["page"] = page_number
    #             all_requirements.append(req_result)

    #     unique_requirements = []
    #     seen = set()
    #     for req in all_requirements:
    #         txt = req["requirement"].strip().lower()
    #         if txt not in seen:
    #             seen.add(txt)
    #             unique_requirements.append(req)

    #     return unique_requirements

    
    def process_pdf(self, pdf_path):
        page_texts = self.pdf_utils.extract_text(pdf_path=pdf_path)
        flat_results = []

        for page_number, page_content in enumerate(page_texts, start=1):
            if page_content and page_content.strip():
                page_reqs = self.process_page(page_content, page_number)
                flat_results.extend(page_reqs)

        return flat_results

    def find_most_similar(self, sentence, page_texts):
        punkt_params = PunktParameters()
        sentence_splitter = PunktSentenceTokenizer(punkt_params)

        best_match = {
            "original_text": "",
            "match_score": 0.0,
            "page": None
        }

        req_embedding = self.embedding_model.encode(sentence, convert_to_tensor=True)

        for page_number, page_content in enumerate(page_texts, start=1):
            sentences = sentence_splitter.tokenize(page_content)
            sentences = [s.strip() for s in sentences if s.strip()]
            if not sentences:
                continue
            
            embeddings = self.embedding_model.encode(sentences, convert_to_tensor=True)
            similarities = util.pytorch_cos_sim(req_embedding, embeddings)[0]
            idx = similarities.argmax().item()
            score = float(similarities[idx])

            if score > best_match["match_score"]:
                best_match = {
                    "original_text": sentences[idx],
                    "match_score": round(score, 4),
                    "page": page_number
                }

        return best_match
    
    def process_sentence(self, sentence):
        encodings = self.multitask_tokenizer([sentence], truncation=True, padding= True, max_length=256, return_tensors="pt")
        input_ids = encodings["input_ids"].to(device)
        attention_mask = encodings["attention_mask"].to(device)

        with torch.no_grad():
            out = self.multitask_model(input_ids=input_ids, attention_mask=attention_mask)

        logits_bin = out["logits_bin"].softmax(dim=1)[0]
        logits_cat = out["logits_cat"].softmax(dim=1)[0]

        label_bin_idx = logits_bin.argmax().item()
        type_req = labelMap.get(f"LABEL_{label_bin_idx}", "Unknown")
        confidence = round(logits_bin[label_bin_idx].item(), 4)

        result = {
            "requirement": sentence,
            "confidence": confidence,
            "type": type_req
        }

        if type_req == "NF":
            label_cat_idx = logits_cat.argmax().item()
            nf_type = nfLabelMap.get(f"LABEL_{label_cat_idx}", "Unknown")
            result["type"] = nf_type
            result["confidence"] = round(logits_cat[label_cat_idx].item(), 4)
        
        return result
    
    def process_manual_requirement(self, sentence, pdf_path):
        result = self.process_sentence(sentence)

        page_texts = self.pdf_utils.extract_text(pdf_path)
        best_match = self.find_most_similar(sentence, page_texts)

        result.update(best_match)
        return result
    
    def process_page(self, page_content, page_number):

        user_req_text = generate_requirements(self.phi4_pipeline, page_content, self.user_prompt)
        system_req_text = generate_requirements(self.phi4_pipeline, page_content, self.system_prompt)

        all_requirements = []

        for req_texts in [user_req_text, system_req_text]:
            sentences = re.split(r"\.\s*", req_texts)
            sentences = [s.strip() for s in sentences if s.strip()]
            for sentence in sentences:
                if not re.match(r"^(As a |The )", sentence.strip(), re.IGNORECASE):
                    continue

                result = self.process_sentence(sentence)
                best_match = self.find_most_similar(sentence, [page_content])

                result.update(best_match)
                result["page"] = page_number

                all_requirements.append(result)

        unique_requirements = []
        seen = set()
        for req in all_requirements:
            txt = req["requirement"].strip().lower()
            if txt not in seen:
                seen.add(txt)
                unique_requirements.append(req)
        
        return unique_requirements

    

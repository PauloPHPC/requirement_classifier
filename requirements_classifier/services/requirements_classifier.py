import torch
import re
import nltk
from sentence_transformers import SentenceTransformer, util
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktParameters
from .pdf_services import PDFUtils
from requirements_classifier.ai.networks import load_phi4_model, load_multitask_classifier, generate_requirements

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
        
        self.user_prompt = """
        You are an expert in extracting USER requirements from texts. The definition of USER is a person who benefits from the system being developed. Your task is to extract and rewrite from the text the software requirements that represents a functionality that the system will give to its user. The format have to be: “As a <user type>, I want to <objective> for <reason>”. Always ignore numbers. Always make each requirement less than two sentences. Always Ignore anything related to technical aspects of the system. 
        """

        self.system_prompt = """
        You are an expert in extracting SYSTEM requirements from texts. The definition of a SYSTEM A set of interacting components that work together to achieve a specific goal or fulfill a defined purpose. The format has to be: “The <system/entity> shall <funcionality> <description>. Always ignore numbers. Always make each requirement less than two sentences. The requirements may have technical aspects of the system”
        """

        
#     def __init__(self, phi4_model_path = "microsoft/phi-4-mini-instruct",
#                  bert_bin_path = "./reqClassifier/services/BERT-Base-Binary",
#                  bert_nf_path = "./reqClassifier/services/BERT-base-NFMulticlass"):
#         """
#         This loads all the models/pipelines all at once, for them to stay on the memory.
#         """
#         self.phi4_pipeline = self.load_phi4_model(phi4_model_path)
#         self.multitask_tokenizer, self.multitask_model = self.load_multitask_classifier(
#             model_name="distilbert-base-uncased",
#             bin_path="./DistilBERT/multitastk_distilbert.bin",
#             tokenizer_path="./DistilBERT/tokenizer.json"  # onde está seu tokenizer.json
#         )
#         self.pdf_utils = PDFUtils()
#         self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
#         nltk.download("punkt")

#         self.user_prompt = """
# You are an expert in extracting USER requirements from texts. The definition of USER is a person who benefits from the system being developed. Your task is to extract and rewrite from the text the software requirements that represents a functionality that the system will give to its user. The format have to be: “As a <user type>, I want to <objective> for <reason>”. Always ignore numbers. Always make each requirement less than two sentences. Always Ignore anything related to technical aspects of the system. 
# """

#         self.system_prompt = """
# You are an expert in extracting SYSTEM requirements from texts. The definition of a SYSTEM A set of interacting components that work together to achieve a specific goal or fulfill a defined purpose. The format have to be: “The <system/entity> shall <funcionality> <description>. Always ignore numbers. Always make each requirement less than two sentences.. The requirements may have technical aspects of the system”
# """


    ###
    # Load Multitask Classifier Model
    ###
    
    # def load_multitask_classifier(self, model_name, bin_path, tokenizer_path):
    #     tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    #     model = BertForMultiTask(
    #         model_name,
    #         num_categories=11,
    #         gamma=2.0
    #     )

    #     state_dict = torch.load(bin_path, map_location=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    #     model.load_state_dict(state_dict)
    #     model.eval().to(device)

    #     return tokenizer, model

    # ###
    # # Load phi-4
    # ###

    # def load_phi4_model(self, model_Path):
    #     """
    #     Loads the phi-4-mini-instruct (Microsoft) from HuggingFace Transformers library.
    #     """
    #     tokenizer = AutoTokenizer.from_pretrained(model_Path)
    #     model = AutoModelForCausalLM.from_pretrained(
    #         model_Path,
    #         torch_dtype=torch.float16,
    #         trust_remote_code= True
    #     ).to(device)

    #     text_gen = pipeline(
    #         "text-generation",
    #         model=model,
    #         tokenizer=tokenizer,
    #         device=0 if device == "cuda" else -1 
    #     )

    #     return text_gen

    # def generate_requirements(self, text, prompt):
    #     """
    #     Uses the Phi4 to generate the requirements based on the text provided by the user.
    #     """
    #     prompt_msg = [{"role": "system", "content": prompt}, {"role": "user", "content": text}]
    #     outputs = self.phi4_pipeline(
    #         prompt, 
    #         max_new_tokens=500, 
    #         do_sample= False, 
    #         temperature= 0.0)
    #     return outputs[0].get("generated_text", "")
    
    def process_sentence(self, sentence, embeddings_sentence, sentences_pages):
        encodings = self.multitask_tokenizer([sentence], truncation=True, padding=True, max_length=256, return_tensors="pt")
        input_ids = encodings["input_ids"].to(device)
        attention_mask = encodings["attention_mask"].to(device)

        with torch.no_grad():
            out = self.multitask_model(input_ids=input_ids, attention_mask=attention_mask)

        logits_bin = out["logits_bin"].softmax(dim=1)[0]
        logits_cat = out["logits_cat"].softmax(dim=1)[0]

        label_bin_idx = logits_bin.argmax().item()
        type_req = labelMap.get(f"LABEL_{label_bin_idx}", "Unknown")
        confidence = round(logits_bin[label_bin_idx].item(), 4)

        req_embedding = self.embedding_model.encode(sentence, convert_to_tensor=True)
        cos_similar = util.pytorch_cos_sim(req_embedding, embeddings_sentence)[0]
        idx_most_similar = cos_similar.argmax().item()

        original_text = sentences_pages[idx_most_similar]
        match_score = round(float(cos_similar[idx_most_similar]), 4)

        result = {
            "requirement": sentence,
            "confidence": confidence,
            "type": type_req,
            "original_text": original_text,
            "match_score": match_score
        }

        if type_req == "NF":
            label_cat_idx = logits_cat.argmax().item()
            nf_type = nfLabelMap.get(f"LABEL_{label_cat_idx}", "Unknown")
            result["type"] = nf_type
            result["confidence"] = round(logits_cat[label_cat_idx].item(), 4)
        
        return result
    
    def process_page(self, page_content, page_number):
        user_req_text = generate_requirements(self.phi4_pipeline, page_content, self.user_prompt)
        system_req_text = generate_requirements(self.phi4_pipeline, page_content, self.system_prompt)

        punkt_param = PunktParameters()
        sentence_splitter = PunktSentenceTokenizer(punkt_param)
        sentences_pages = sentence_splitter.tokenize(page_content)
        sentences_pages = [s.strip() for s in sentences_pages if s.strip()]
        embeddings_sentences = self.embedding_model.encode(sentences_pages, convert_to_tensor=True)

        all_requirements = []

        for req_text in [user_req_text, system_req_text]:
            sentences = re.split(r"\.\s*", req_text)
            sentences = [s.strip() for s in sentences if s.strip()]
            for sentence in sentences:
                req_result = self.process_sentence(
                    sentence,
                    embeddings_sentences,
                    sentences_pages
                )
                req_result["page"] = page_number
                all_requirements.append(req_result)

        return all_requirements

    
    def process_pdf(self, pdf_path):
        page_texts = self.pdf_utils.extract_text(pdf_path=pdf_path)
        flat_results = []

        for page_number, page_content in enumerate(page_texts, start=1):
            if page_content and page_content.strip():
                page_reqs = self.process_page(page_content, page_number)
                flat_results.extend(page_reqs)

        return flat_results


    # def check_requirements(self, text, system_instructions):
    #     """
    #     Executes the phi-4-mini-instruct to generate the requirements based on a prompt.
    #     This should execute on GPU for ultimate performance.
    #     """

    #     # Gerar saída
    #     prompt = [
    #         {"role": "system", "content" : system_instructions},
    #         {"role": "user", "content": text}
    #     ]

    #     outputs = self.phi4_pipeline(
    #         prompt, 
    #         max_new_tokens=500, 
    #         do_sample= False, 
    #         temperature= 0.0)
        
    #     role_content_list = outputs[0]["generated_text"]
        
    #     assistant_text = ""
    #     for item in role_content_list:
    #         if item.get("role") == "assistant":
    #             assistant_text = item.get("content", "")
    #             break

    #     return assistant_text

    # def process_pdf(self, pdf_path):
    #     """
    #     Primary function:
    #     1 - Extract texts from PDF file
    #     2 - Generate requirements (User + System) with phi-4-mini
    #     3 - Divide into sentences
    #     4 - Classify each sentence:
    #         - Head 1: Binary F vs NF
    #         - Head 2: Multiclass NF (only for NF sentences)
    #     Returns:
    #         flat_results: list of dicts per requirement
    #     """
    #     page_texts = self.pdf_utils.extract_text(pdf_path=pdf_path)
    #     requirements_per_page = {}

    #     for i, page_content in enumerate(page_texts, start=1):
    #         page_key = i

    #         if page_content and page_content.strip():
    #             # Gera requisitos com phi-4
    #             user_req_text = self.check_requirements(page_content, self.user_prompt)
    #             system_req_text = self.check_requirements(page_content, self.system_prompt)

    #             # Divide página em frases para similaridade
    #             punkt_param = PunktParameters()
    #             sentence_splitter = PunktSentenceTokenizer(punkt_param)
    #             sentences_pages = sentence_splitter.tokenize(page_content)
    #             sentences_pages = [s.strip() for s in sentences_pages if s.strip()]
    #             embeddings_sentences = self.embedding_model.encode(sentences_pages, convert_to_tensor=True)

    #             all_requirements = []

    #             for req_text, req_origin in [(user_req_text, "User"), (system_req_text, "System")]:
    #                 # Divide texto gerado em frases
    #                 sentences = re.split(r"\.\s*", req_text)
    #                 sentences = [s.strip() for s in sentences if s.strip()]
    #                 if not sentences:
    #                     continue

    #                 # Tokenize inputs
    #                 encodings = self.multitask_tokenizer(
    #                     sentences,
    #                     truncation=True,
    #                     padding=True,
    #                     max_length=256,
    #                     return_tensors="pt"
    #                 )

    #                 input_ids = encodings["input_ids"].to(self.multitask_model.device)
    #                 attention_mask = encodings["attention_mask"].to(self.multitask_model.device)

    #                 with torch.no_grad():
    #                     out = self.multitask_model(
    #                         input_ids=input_ids,
    #                         attention_mask=attention_mask
    #                     )

    #                 logits_bin = out["logits_bin"].softmax(dim=1)
    #                 logits_cat = out["logits_cat"].softmax(dim=1)

    #                 # Para cada frase
    #                 for idx, sent in enumerate(sentences):
    #                     pred_bin = logits_bin[idx]
    #                     label_bin_idx = pred_bin.argmax().item()
    #                     score_bin = pred_bin[label_bin_idx].item()

    #                     # Head 1: F vs NF
    #                     label_bin = f"LABEL_{label_bin_idx}"
    #                     type_req = labelMap.get(label_bin, "Unknown")

    #                     # Similaridade com texto original
    #                     req_embedding = self.embedding_model.encode(sent, convert_to_tensor=True)
    #                     cos_similar = util.pytorch_cos_sim(req_embedding, embeddings_sentences)[0]
    #                     idx_most_similar = cos_similar.argmax().item()
    #                     original_text = sentences_pages[idx_most_similar]
    #                     score_match = float(cos_similar[idx_most_similar])

    #                     result_dict = {
    #                         "requirement": sent,
    #                         "confidence": round(score_bin, 4),
    #                         "type": type_req,
    #                         "original_text": original_text,
    #                         "match_score": round(score_match, 4),
    #                         "page": page_key
    #                     }

    #                     # Head 2: Multiclass NF (apenas se NF)
    #                     if type_req == "NF":
    #                         pred_cat = logits_cat[idx]
    #                         label_cat_idx = pred_cat.argmax().item()
    #                         score_cat = pred_cat[label_cat_idx].item()

    #                         label_nf = f"LABEL_{label_cat_idx}"
    #                         nf_type = nfLabelMap.get(label_nf, "Unknown")

    #                         result_dict["type"] = nf_type
    #                         result_dict["confidence"] = round(score_cat, 4)

    #                     all_requirements.append(result_dict)

    #             requirements_per_page[page_key] = all_requirements
    #         else:
    #             requirements_per_page[page_key] = []

    #     # Flatten results
    #     flat_results = []
    #     for page_key, reqs in requirements_per_page.items():
    #         for req in reqs:
    #             flat_results.append(req)

    #     return flat_results

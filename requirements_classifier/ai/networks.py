import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
from requirements_classifier.ai.classifier import BertForMultiTask

device = "cuda" if torch.cuda.is_available() else "cpu"

def load_multitask_classifier(model_name, bin_path, tokenizer_path):
    """
    Loads the multitask learning model, in this version DistilBERT.
    """
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_path)

    model = BertForMultiTask(
        model_name,
        num_categories=11,
        gamma=2.0
    )

    state_dict = torch.load(bin_path, map_location=torch.device("cuda" if torch.cuda.is_available() else "cpu"))
    model.load_state_dict(state_dict)
    model.eval().to(device)

    return tokenizer, model

def load_phi4_model(model_Path):
    """
    Loads the phi-4-mini-instruct (Microsoft) from HuggingFace Transformers library.
    """
    tokenizer = AutoTokenizer.from_pretrained(model_Path)
    model = AutoModelForCausalLM.from_pretrained(
        model_Path,
        torch_dtype=torch.float16,
        trust_remote_code= True
    ).to(device)

    text_gen = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device=0 if device == "cuda" else -1 
    )

    return text_gen

def generate_requirements(phi_pipeline, text, prompt):
    """
    Uses Phi-4-mini-instruct to generate requirements.
    Always returns a string (content of the assistant).
    """
    prompt_msg = [{"role": "system", "content": prompt}, {"role": "user", "content": text}]

    outputs = phi_pipeline(
        prompt_msg,
        max_new_tokens=500,
        do_sample=False,
        temperature=0.0
    )

    generated = outputs[0].get("generated_text", [])

    if isinstance(generated, str):
        # raríssimo, mas ok
        return generated

    elif isinstance(generated, list):
        # caso correto: uma lista de roles
        for item in generated:
            if item.get("role") == "assistant":
                return item.get("content", "")
        # fallback: nenhum "assistant" encontrado
        return ""
    else:
        # fallback: tipo inesperado
        return ""
# requirement_classifier

The *requirement_classifier* tool uses two AI models for documenting requirements from a PDF source and classifying them according to the PROMISE+ dataset classification (Functional and Non-Functional classes like Security, Availability, Maintainability...).

The models are:
* Phi-4-mini-instruct by [Microsoft](https://huggingface.co/microsoft/Phi-4-mini-instruct) for the requirement documentation.
* A trained version of [distilbert](https://huggingface.co/distilbert/distilbert-base-uncased) for classification.

## Requirements
Since this tool uses AI models heavily, the recommended setups are:
- Python 3.12;
- Linux or Windows systems;
- NVIDIA GPU with 12+ GB of VRAM[^1].

## How to run (developer version):

### 1. Clone this repository
```bash
git clone https://github.com/PauloPHPC/requirement_classifier.git
```

### 2. Access the cloned repository
```bash
cd requirement_classifier
```

### 3. Generate a Python venv and install requirements.txt

- Windows (CMD):
```Batchfile
python3 -m venv venv
venv/Scripts/activate.bat
pip install -r requirements.txt
```

- Windows (Powershell):
```PowerShell
python3 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

- Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Download the requirements classifier model and generate .env with django secret key[^2]

```bash
python project_config.py
```
>[!CAUTION]
>Make sure .env is in .gitignore!

### 5. Migrate the database tables
```bash
python manage.py migrate
```

### 6. Run the server
```bash
python manage.py runserver 0.0.0.0:8000
```

[^1]: It may run with less VRAM on Windows (using part of the system RAM) but performance can degrade significantly
[^2]: The requirements classifier model is avalible at [HuggingFace](https://huggingface.co/PauloHPCerqueira/distillbert-requirements-classifier-mtl)
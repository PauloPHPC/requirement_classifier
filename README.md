# requirement_classifier

The *requirement_classifier* tool uses two AI models for documenting requirements from a PDF source and classifying them according with the PROMISE+ dataset classification (Functional and Non-Functional classes like Security, Availability, Maintainability...).

## Requirements
Since this tool uses AI models heavily, the recommended setups are:
- Python 3.12;
- Linux or Windows systems;
- NVIDIA GPU with 12+ GB of VRAM are recommended.\
*(It may run with less VRAM on Windows (using part of the systems RAM) but performance can degrade signifcantly)*

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

- Windows:
```bash
python3 -m venv venv
cmd: venv/Scripts/activate.bat
powershell: venv/Scripts/activate
pip install -r requirements.txt
```

- Linux:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Download the requirements classifier model and generate .env with django secret key
*The requirements classifier model are avalible at [HuggingFace](https://huggingface.co/PauloHPCerqueira/distillbert-requirements-classifier-mtl)*
```python
python project_config.py
```

### 5. Migrate the database tables
```python
python manage.py migrate
```

### 6. Run the server
```python
python manage.py runserver 0.0.0.0:8000
```
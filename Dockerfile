FROM pytorch/pytorch:2.7.1-cuda12.6-cudnn9-runtime

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install gunicorn

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD [ "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000" ]
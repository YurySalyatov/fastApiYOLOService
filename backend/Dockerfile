FROM python:3.11-slim

WORKDIR /usr/backend/app

COPY ./requirements.txt /usr/backend/app/requirements.txt

RUN apt-get update && apt-get install -y \
    libgl1 \
    ffmpeg
RUN rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r /usr/backend/app/requirements.txt

COPY . /usr/backend/app/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
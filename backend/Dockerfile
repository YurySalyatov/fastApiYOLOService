FROM python:3.11-slim



WORKDIR /usr/backend/app

COPY ./requirements.txt /usr/backend/app/requirements.txt
#RUN set -eux \
#    && apk add --no-cache --virtual .build-deps build-base \
#         openssl-dev libffi-dev gcc musl-dev python3-dev \
#    && pip install --upgrade pip setuptools wheel \
#    && pip install -r /usr/src/app/requirements.txt \
#    && rm -rf /root/.cache/pip
RUN apt-get update && apt-get install -y \
    libgl1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r /usr/backend/app/requirements.txt

COPY . /usr/backend/app/

#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
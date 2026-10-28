# Hojas de campo (Pixilate, Docker en WSL). Solo FastAPI: los datos llegan montados de solo lectura.
FROM python:3.12.7-slim-bookworm
RUN pip install --no-cache-dir fastapi==0.142.2 uvicorn==0.30.6 pydantic==2.13.5 \
 && useradd --create-home --uid 10001 campo && mkdir /datos && chown campo /datos
WORKDIR /app
COPY backend.py ./
COPY static ./static
USER campo
ENV PYTHONDONTWRITEBYTECODE=1
EXPOSE 8049
# 0.0.0.0 solo dentro de la red del contenedor; en el host Compose lo publica en 127.0.0.1
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8049"]

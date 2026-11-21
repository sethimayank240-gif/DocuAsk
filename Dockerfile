# Stage 1: build the React frontend
FROM node:20-slim AS frontend
WORKDIR /fe
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Flask backend that also serves the built frontend
FROM python:3.11-slim
RUN useradd -m -u 1000 user
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
COPY --from=frontend /fe/dist ./static
ENV DATA_DIR=/tmp/data STATIC_DIR=/app/static PYTHONUNBUFFERED=1
USER user
EXPOSE 7860
# One worker: documents are kept in a single JSON store.
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--workers", "1", "--threads", "4", "--timeout", "120", "app:create_app()"]

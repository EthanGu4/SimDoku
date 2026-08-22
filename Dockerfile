# Single-image deployment: the frontend is built here and served by the
# backend, so there is one process, one port, and no CORS to configure.

# --- build the frontend -----------------------------------------------------
FROM node:22-slim AS frontend

WORKDIR /frontend
# .npmrc carries legacy-peer-deps, without which `npm ci` fails on
# openapi-typescript's stale TypeScript peer range. See the file for detail.
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- runtime ----------------------------------------------------------------
FROM python:3.11-slim

# tesseract-ocr is a system binary, not a pip package, and is what the photo
# board detection shells out to. libglib2.0-0 is opencv's one remaining shared
# library even in the headless build.
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install torch from the CPU wheel index first. Plain `pip install torch` on
# Linux pulls the CUDA build and its NVIDIA dependencies, which is several GB
# of image for a 9x9 board that never touches a GPU. Installing it up front
# means the requirements.txt line below is already satisfied.
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY --from=frontend /frontend/dist ./static

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

# Hosts that inject their own $PORT (Render, Railway, Cloud Run) are honored;
# otherwise this falls back to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

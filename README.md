# SimDoku
Sudoku simulation because why not

## Development

Prerequisites: Python 3.11+, Node, and [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) on your PATH (used for photo-based board detection — install via `winget install --id UB-Mannheim.TesseractOCR -e` on Windows, or `brew install tesseract` / `apt install tesseract-ocr` elsewhere).

First-time setup:

```
cd backend && python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt
cd frontend && npm install
cd .. && npm install
```

Then, from the repo root, run both the backend (`:8000`) and frontend (`:5173`) together:

```
npm run dev
```

Or run them separately — `uvicorn app.main:app --reload --port 8000` in `backend/` (venv active), `npm run dev` in `frontend/`.

The `neural_net` solver loads pretrained weights committed at `backend/app/ml/weights/neural_solver.pt` — no training needed to run the app. To retrain it (e.g. after changing the model architecture in `app/ml/sudoku_cnn.py`), run `python -m scripts.train_neural_solver` from `backend/` with the venv active; it regenerates its own synthetic training puzzles, so no dataset download is needed.

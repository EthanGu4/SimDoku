# SimDoku
Sudoku simulation because why not

## Development

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

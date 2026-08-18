"""Dumps the FastAPI app's OpenAPI schema to backend/openapi.json.

Run after changing any request/response model so the frontend can regenerate
its types (`npm run gen:types` in frontend/) instead of hand-duplicating them.
"""

import json
from pathlib import Path

from app.main import app

output_path = Path(__file__).resolve().parent.parent / "openapi.json"
output_path.write_text(json.dumps(app.openapi(), indent=2) + "\n")
print(f"wrote {output_path}")

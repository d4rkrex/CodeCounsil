"""
Ambiguous project — authorization exists but may be in external middleware.
CodeCounsil should produce probable_risk with low/medium confidence,
NOT confirmed_finding. The correct output depends on context not in the repo.
"""

from fastapi import FastAPI, Request

app = FastAPI()

# Authorization is enforced by the API Gateway (Kong) before reaching this service.
# The service itself doesn't re-check — this is intentional for this architecture.
# However, there is no documentation of this in the code.

@app.get("/documents/{doc_id}")
async def get_document(doc_id: int, request: Request):
    # No explicit auth check here — relies on upstream API Gateway
    # Is this safe? Depends on deployment topology, not visible in this code.
    doc = _fetch_document(doc_id)
    return doc


@app.post("/documents/{doc_id}/share")
async def share_document(doc_id: int, recipient_email: str, request: Request):
    # Same pattern — no in-code auth check
    _share_document(doc_id, recipient_email)
    return {"shared": True}


def _fetch_document(doc_id: int) -> dict:
    return {"id": doc_id, "content": "...", "owner_id": 1}


def _share_document(doc_id: int, email: str):
    pass

"""
domains.py — Domain library endpoints (listing + custom upload).
"""

import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

router = APIRouter(prefix="/api")

DOMAINS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "domains")


@router.get("/domains")
async def list_domains_full():
    """Return all domains with metadata (name, description, source)."""
    from pddl_tool.classifier import list_available_domains, DOMAIN_DESCRIPTIONS
    names = sorted(list_available_domains())
    return {
        "domains": [
            {
                "name": n,
                "description": DOMAIN_DESCRIPTIONS.get(n, ""),
                "source": "builtin",
            }
            for n in names
        ]
    }


@router.post("/domains/upload")
async def upload_domain(
    file: UploadFile = File(...),
    description: str = Form(""),
):
    """Accept a PDDL domain file upload and add it to the library."""
    if not file.filename or not file.filename.endswith(".pddl"):
        raise HTTPException(status_code=400, detail="File must be a .pddl file.")

    raw = await file.read()
    try:
        pddl_text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be valid UTF-8 text.")

    low = pddl_text.lower()
    if "(define" not in low or "(domain" not in low:
        raise HTTPException(
            status_code=400,
            detail="Does not look like a valid PDDL domain — missing (define (domain ...)).",
        )

    from pddl_tool.classifier import extract_domain_name, save_domain_to_library
    name = extract_domain_name(pddl_text)
    saved_name = save_domain_to_library(name, pddl_text, description or f"User-uploaded domain: {name}")

    return {"name": saved_name, "message": f"Domain '{saved_name}' uploaded successfully."}

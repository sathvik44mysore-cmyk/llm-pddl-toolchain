"""
classifier.py — Match a natural language task to a domain in the library.
Uses the LLM to pick the best domain, falls back to full generation if none fits.
"""

import os
import json
from groq import Groq
from .generator import _get_client

DOMAINS_DIR = os.path.join(os.path.dirname(__file__), "..", "domains")

# Short descriptions shown to the LLM for classification
DOMAIN_DESCRIPTIONS = {
    # Hand-crafted domains
    "blocksworld": "Stacking, unstacking, picking up and putting down blocks on a table",
    "logistics":   "Moving packages between cities using trucks and airplanes",
    "gripper":     "Robot with grippers moving balls between rooms",
    "rover":       "Mars rover navigating terrain, sampling rocks/soil, taking images",
    "ferry":       "Ferry transporting cars between locations across a river",
    "hanoi":       "Towers of Hanoi — moving disks between pegs respecting size order",
    "depots":      "Forklifts and trucks moving crates between depots and distributors",
    "satellite":   "Satellite pointing instruments at targets and taking images",
    "freecell":    "Freecell card game — moving cards between columns and free cells",
    "tyreworld":   "Changing tyres on a car — jacking, loosening, removing, replacing",
    # IPC validated domains (preferred — use _ipc suffix variants when matched)
    "blocksworld_ipc": "Stacking, unstacking, picking up and putting down typed blocks (IPC 2000)",
    "logistics_ipc":   "Moving packages between cities via trucks and airplanes (IPC 2000)",
    "freecell_ipc":    "Freecell card game — typed version (IPC 2000)",
    "depots_ipc":      "Forklifts and trucks move crates between depots (IPC 2002)",
    "driverlog":       "Drivers move trucks along roads and walk between locations (IPC 2002)",
    "zenotravel":      "Aircraft carry passengers between cities (IPC 2002)",
    "satellite_ipc":   "Satellite takes images of targets using calibrated instruments (IPC 2002)",
    "rovers":          "Rovers navigate terrain, sample soil and rock, transmit data (IPC 2002)",
}


def load_domain_pddl(name: str) -> str | None:
    """Load a built-in domain PDDL file by name."""
    path = os.path.join(DOMAINS_DIR, f"{name}.pddl")
    if os.path.exists(path):
        with open(path) as f:
            return f.read()
    return None


def list_available_domains() -> list[str]:
    """Return names of all available built-in domains."""
    if not os.path.isdir(DOMAINS_DIR):
        return []
    return [
        f[:-5] for f in os.listdir(DOMAINS_DIR)
        if f.endswith(".pddl")
    ]


def classify_domain(task: str, available: list[str] | None = None) -> str | None:
    """
    Ask the LLM which domain best fits the task.

    Returns the domain name if confident, or None if no good match.
    """
    if available is None:
        available = list_available_domains()

    if not available:
        return None

    desc_lines = "\n".join(
        f'  "{name}": "{DOMAIN_DESCRIPTIONS.get(name, "")}"'
        for name in available
        if name in DOMAIN_DESCRIPTIONS
    )

    prompt = f"""Given this planning task:
"{task}"

Choose the most suitable domain from this list, or say "none" if no domain fits well:
{{{desc_lines}}}

Reply with ONLY a JSON object like:
{{"domain": "blocksworld", "confidence": "high"}}
or
{{"domain": "none", "confidence": "low"}}

Confidence is "high" if the task clearly matches, "low" if it's a stretch."""

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=64,
    )

    raw = response.choices[0].message.content.strip()

    # Strip markdown code block if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    try:
        result = json.loads(raw)
        domain = result.get("domain", "none")
        confidence = result.get("confidence", "low")
        if domain == "none" or confidence == "low":
            return None
        if domain in available:
            return domain
    except (json.JSONDecodeError, KeyError):
        pass

    return None


def get_domain_for_task(task: str) -> tuple[str | None, str | None]:
    """
    Try to match task to a library domain.

    Returns:
        (domain_name, domain_pddl) if a match is found, else (None, None)
    """
    available = list_available_domains()
    name = classify_domain(task, available)
    if name:
        pddl = load_domain_pddl(name)
        if pddl:
            return name, pddl
    return None, None


def extract_domain_name(domain_pddl: str) -> str:
    """Extract the domain name from a PDDL domain string."""
    import re
    m = re.search(r"\(define\s+\(domain\s+([\w-]+)\)", domain_pddl, re.IGNORECASE)
    return m.group(1).lower().replace(" ", "-") if m else "generated"


def save_domain_to_library(name: str, domain_pddl: str, description: str = "") -> str:
    """
    Save a generated domain PDDL to the domains directory.
    Appends a numeric suffix if a file with that name already exists.
    Returns the final name used.
    """
    os.makedirs(DOMAINS_DIR, exist_ok=True)
    base = name
    suffix = 1
    candidate = base
    while os.path.exists(os.path.join(DOMAINS_DIR, f"{candidate}.pddl")):
        candidate = f"{base}_{suffix}"
        suffix += 1
    path = os.path.join(DOMAINS_DIR, f"{candidate}.pddl")
    with open(path, "w") as f:
        f.write(domain_pddl)
    if candidate not in DOMAIN_DESCRIPTIONS and description:
        DOMAIN_DESCRIPTIONS[candidate] = description
    return candidate

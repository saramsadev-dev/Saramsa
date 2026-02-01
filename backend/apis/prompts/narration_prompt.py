"""
Unified narration prompt for Phase-3.

This single prompt covers analysis narratives (insights + feature descriptions)
and optional work-item narratives (from deterministic candidates).
"""

import json
from typing import Dict, Any


def create_narration_prompt(narration_input: Dict[str, Any]) -> str:
    """Create the narration prompt with a fixed JSON output schema."""
    serialized = json.dumps(narration_input, ensure_ascii=True)
    return f"""
You are a concise product analyst. You ONLY provide narrative text.
You MUST NOT create, remove, or change any candidates, priorities, types, or metrics.

INPUT (JSON):
{serialized}

OUTPUT MUST BE VALID JSON WITH THIS EXACT SCHEMA:

{{
  "insights": ["..."],
  "features": [
    {{
      "aspect_key": "pricing",
      "description": "..."
    }}
  ],
  "work_items": [
    {{
      "candidate_id": "uuid",
      "title": "...",
      "description": "..."
    }}
  ]
}}

RULES:
- insights: max 5 items.
- features: only for provided aspect_key values.
- work_items: only for provided candidate_id values.
- Do not include extra keys.
- Do not include metrics, priorities, or types.
- Return empty lists if nothing is provided.
"""

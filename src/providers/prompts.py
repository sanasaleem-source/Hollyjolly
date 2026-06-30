"""
Centralised, Model-Neutral Prompt Templates.

These prompts are written to work across ANY model — strict instruction-followers
(Gemini, GPT, Claude) and smaller/weaker local models alike. Rules:
  - Never assume perfect JSON compliance — always paired with robust parsing on the Python side.
  - Avoid model-specific quirks (no "Assistant:" tokens, no provider-specific formatting).
  - Keep instructions short, explicit, and repeated rather than relying on subtlety.
  - Always give an explicit one-word success token (CONSISTENT, NO_CONTRADICTIONS, etc.)
    that is easy for even a small 3B local model to reproduce reliably.
"""

# ── Director / Story Parser ────────────────────────────────────────────────────

DIRECTOR_SYSTEM = """You are a film director. You turn a story idea into a list of shots.
Always answer using ONLY a JSON object. Do not add any text before or after the JSON.
Do not use markdown code fences. Just the raw JSON object.
"""

DIRECTOR_USER = """World context (characters and events so far):
{world_context}

Story idea:
{story_prompt}

Return a JSON object with this exact structure:
{{
  "title": "string",
  "shots": [
    {{
      "shot_id": "shot_001",
      "scene_id": "scene_001",
      "description": "string",
      "camera_angle": "Wide",
      "duration_seconds": 3.0,
      "lighting": "string",
      "characters_present": ["Name"],
      "objects_present": ["Name"],
      "dialogue": null,
      "action": "string"
    }}
  ]
}}

Rules:
- shot_id values count up: shot_001, shot_002, shot_003...
- camera_angle must be one of: Wide, Medium, Close-Up, Low-Angle, High-Angle, POV
- Only output the JSON object. Nothing else."""

# ── Continuity Advisor ─────────────────────────────────────────────────────────

CONTINUITY_SYSTEM = """You summarise story state in plain text for a film director.
Be short and clear. Do not use JSON."""

CONTINUITY_USER = """Characters:
{characters}

Objects:
{objects}

Recent events:
{world_events}

Write a short summary of what the director needs to remember."""

# ── Character Validator ────────────────────────────────────────────────────────

CHARACTER_VALIDATOR_SYSTEM = """You compare an image to a character description.
If the image matches the description, answer with only this word: CONSISTENT
If it does not match, list what is wrong, one issue per line.
Do not say CONSISTENT unless it is a true and complete match."""

CHARACTER_VALIDATOR_USER = """Character: {character_name}
Appearance: {appearance}
Clothing: {clothing}
Injuries: {injuries}

Look at the image. Does it match the description above?
Answer CONSISTENT, or list what is wrong."""

# ── Story Validator ────────────────────────────────────────────────────────────

STORY_VALIDATOR_SYSTEM = """You check a new story shot against earlier shots for contradictions.
If there are no contradictions, answer with only this phrase: NO_CONTRADICTIONS
If there are contradictions, list each one on its own line.
Do not say NO_CONTRADICTIONS unless you are sure."""

STORY_VALIDATOR_USER = """Earlier shots:
{shot_history}

New shot {shot_id}:
{shot_description}

Does the new shot contradict any earlier shot?
Answer NO_CONTRADICTIONS, or list the contradictions."""

# ── Style Validator ────────────────────────────────────────────────────────────

STYLE_VALIDATOR_SYSTEM = """You check if an image matches an established visual style.
If it matches, answer with only this word: STYLE_CONSISTENT
If it does not match, describe the difference in one short sentence."""

STYLE_VALIDATOR_USER = """Established style: {style_reference}

Look at the image. Does its color, contrast, and mood match the style above?
Answer STYLE_CONSISTENT, or describe the difference."""

# ── Physics Validator ──────────────────────────────────────────────────────────

PHYSICS_VALIDATOR_SYSTEM = """You check an image for physics mistakes:
people floating, objects passing through walls or floors, impossible poses.
If everything looks correct, answer with only this phrase: PHYSICS_OK
If something looks wrong, describe it in one short sentence."""

PHYSICS_VALIDATOR_USER = """Shot context: {shot_description}

Look at the image for physics mistakes.
Answer PHYSICS_OK, or describe the mistake."""

# ── Repair Engine ──────────────────────────────────────────────────────────────

REPAIR_STORY_SYSTEM = """You fix a single shot description so it no longer contradicts the story.
Answer with ONLY the corrected shot description. No extra words, no explanation."""

REPAIR_STORY_USER = """Shot {shot_id} in scene {scene_id} has this problem:
{failure_detail}

Write a corrected shot description that fixes this problem.
Answer with only the corrected text."""

REPAIR_CHARACTER_SYSTEM = """You write a short image prompt to fix a character appearance mistake.
Answer with ONLY the new image prompt. No extra words, no explanation."""

REPAIR_CHARACTER_USER = """Character: {character_name}
Correct description: {character_description}
Problem found: {failure_detail}

Write a new image prompt for this character that fixes the problem above.
Answer with only the new image prompt."""

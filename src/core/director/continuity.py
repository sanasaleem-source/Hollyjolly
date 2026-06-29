"""
Continuity Advisor — compiles World State into a context string for the Director.
Uses centralised prompts from src/providers/prompts.py.
"""
import json
import logging
from src.providers.prompts import CONTINUITY_SYSTEM, CONTINUITY_USER

logger = logging.getLogger(__name__)


class ContinuityAdvisor:
    """Reads World State and summarises it for Director continuity context."""

    def __init__(self, world_state_manager) -> None:
        self.world_state = world_state_manager

    def compile_continuity_context(self) -> str:
        """Return a plain-text continuity summary for the Director prompt."""
        try:
            characters  = self.world_state.get_all_characters()
            objects     = self.world_state.get_all_objects()
            world_events = self.world_state.get_world_events()

            if not characters and not objects and not world_events:
                return "No prior context — this is the beginning of the production."

            char_text = json.dumps(
                [c.model_dump() for c in characters], indent=2
            ) if characters else "None yet."

            obj_text = json.dumps(
                [o.model_dump() for o in objects], indent=2
            ) if objects else "None yet."

            event_text = json.dumps(
                [e.model_dump() for e in world_events[-5:]], indent=2
            ) if world_events else "None yet."

            # Return a structured string — not calling LLM here to save tokens
            return (
                f"CHARACTERS:\n{char_text}\n\n"
                f"OBJECTS:\n{obj_text}\n\n"
                f"RECENT WORLD EVENTS:\n{event_text}"
            )
        except Exception as e:
            logger.error(f"Continuity compile failed: {e}")
            return "World State unavailable."

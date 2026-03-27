import logging
from myth_weaver.intent_parser import parse_intent
from myth_weaver.game_engine import handle_active_hint, prepare_storyteller_prompt

logger = logging.getLogger(__name__)

def process_user_input(user_input: str, db_session) -> str:
    """
    Evaluates raw user input, routes special commands, and orchestrates the Two-Pass Action Loop.
    """
    user_input = user_input.strip()

    # The system must support active hints via a /hint command
    if user_input.lower() == "/hint":
        logger.info("Player requested an active hint: %s", {"command": user_input})
        return handle_active_hint(db_session)

    try:
        # Pass 1: The Intent Classifier
        intent = parse_intent(user_input)
        
        # Placeholder for Mechanics Resolution (RollForge)
        # If intent.get("requires_rollforge") is True, we would call the C++ engine here.
        rollforge_result = "Action parsed. No mechanic execution integrated in this pass."

        # Pass 2: The Storyteller prompt assembly
        prompt = prepare_storyteller_prompt(
            db_session,
            intent_summary=intent.get("intent_summary", "Unknown action"),
            rollforge_result=rollforge_result
        )
        
        # Note: Sending the assembled prompt to Ollama's chat API will happen here.
        # For now, returning the prompt satisfies the orchestrator flow.
        return prompt

    except Exception as e:
        logger.error("Failed to process user input: %s", {"error": str(e), "input": user_input})
        return "The DM seems confused by that action. Please try again."
import json
import logging
import ollama

logger = logging.getLogger(__name__)

def parse_intent(user_input: str) -> dict:
    """
    Parses user raw text into a structured JSON intent.
    The Intent Parser uses a fast, low parameter LLM.
    """
    system_prompt = (
        "You are an Intent Parser. Respond ONLY with a JSON object containing: "
        "'action_type' (string), 'target' (string or null), 'tool_or_weapon' (string or null), "
        "'intent_summary' (string), and 'requires_rollforge' (boolean). "
        "If it is a combat or skill check, requires_rollforge is true."
    )
    
    try:
        response = ollama.chat(
            model="llama3",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ],
            format="json"
        )
        
        intent_json = response.get("message", {}).get("content", "{}")
        return json.loads(intent_json)
        
    except json.JSONDecodeError as e:
        logger.error("Failed to decode JSON from Intent Parser: %s", {"error": str(e), "input": user_input})
        raise
    except Exception as e:
        logger.error("Intent parsing failed: %s", {"error": str(e)})
        raise
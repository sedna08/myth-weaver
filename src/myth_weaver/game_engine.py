import logging
import ollama

try:
    import rollforge
except ImportError:
    rollforge = None

logger = logging.getLogger(__name__)

def prepare_storyteller_prompt(db_session, intent_summary: str, rollforge_result: str) -> str:
    """
    Dynamically assembles the System Prompt for the Storyteller LLM (Pass 2)
    to prevent hallucinations by injecting the current game state.
    """
    try:
        state = db_session.get_current_state()
        milestone = db_session.get_active_milestone()

        prompt = f"""[SYSTEM DIRECTIVE]
You are the Dungeon Master for a text based roleplaying game. Your job is to describe the world, play the NPCs, and narrate the outcome of the player's actions.
You must not make decisions for the player.
You must adhere strictly to the CURRENT GAME STATE.

[CURRENT GAME STATE]
Location: {state.get('location', 'Unknown')}
Time of Day: {state.get('time_of_day', 'Unknown')}
Player HP: {state.get('player_current_hp', 0)} / {state.get('player_max_hp', 0)}
NPCs Present: {state.get('npcs', 'None')}

[ACTIVE CAMPAIGN CONTEXT]
Current Objective: {milestone}

[ROLLFORGE MECHANICS RESULT]
The player attempted to: {intent_summary}
The internal game engine calculated the result: {rollforge_result}

[INSTRUCTION]
Based on the RollForge result and the Current Game State, narrate the outcome of the player's action in 2 to 3 paragraphs. Stay in character."""
        
        return prompt
    except Exception as e:
        logger.error("Failed to prepare storyteller prompt: %s", {"error": str(e)})
        raise

def handle_active_hint(db_session) -> str:
    """
    Bypasses the Intent Parser to directly request a contextual hint from the LLM.
    """
    prompt = (
        "The player has requested a hint. Look at the [ACTIVE CAMPAIGN CONTEXT] "
        "and provide a subtle, atmospheric clue pointing them toward their current objective. "
        "Do not break character."
    )
    
    try:
        response = ollama.chat(
            model="llama3",
            messages=[{"role": "system", "content": prompt}]
        )
        return response.get("message", {}).get("content", "")
    except Exception as e:
        logger.error("Failed to generate active hint: %s", {"error": str(e)})
        raise

def check_passive_hints(turns: int, perception_score: int) -> tuple[bool, str]:
    """
    Triggered by the engine. Checks if the player has been stuck for > 10 turns.
    If so, rolls a passive perception check to volunteer a hint.
    """
    if turns > 10:
        if not rollforge:
            logger.error("Rollforge module not available for passive hint check: %s", {})
            return False, ""
            
        modifier = (perception_score - 10) // 2
        roll = rollforge.Dice.roll(20)
        
        if roll + modifier >= 10:
            directive = "The player's passive perception has noticed something helpful. Volunteer a clue about their surroundings."
            logger.info("Passive hint check triggered and passed: %s", {"turns": turns, "passed": True})
            return True, directive
            
        logger.info("Passive hint check triggered but failed: %s", {"turns": turns, "passed": False})
        
    return False, ""
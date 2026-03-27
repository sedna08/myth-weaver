import logging
import click
from unittest.mock import MagicMock

from myth_weaver.intent_parser import parse_intent
from myth_weaver.game_engine import handle_active_hint, prepare_storyteller_prompt
from myth_weaver.storyteller import generate_campaign_bible

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """Myth Weaver: LLM Dungeon Master"""
    pass

@cli.command(name="start")
@click.option("--theme", default="Dark Fantasy", help="The theme of the campaign.")
def start_game(theme: str):
    """Start a new game session and generate the Campaign Bible."""
    click.echo(f"Starting new {theme} campaign...")
    
    # Temporary mock session until we wire up the real PostgreSQL connection
    db_session = MagicMock()
    
    # Generate the campaign bible
    generate_campaign_bible(theme, db_session)
    
    # The Interactive Game Loop
    while True:
        try:
            # click.prompt handles standard input cleanly
            user_input = click.prompt("What do you do?", prompt_suffix="\n> ").strip()
        except (EOFError, click.exceptions.Abort):
            # Gracefully handle Ctrl+C or empty inputs from test runners
            break
            
        if user_input.lower() in ["quit", "exit"]:
            click.echo("Ending session. Farewell, adventurer.")
            break
            
        # The system must support active hints via a /hint command
        if user_input.lower() == "/hint":
            logger.info("Player requested an active hint: %s", {"command": user_input})
            hint = handle_active_hint(db_session)
            click.echo(hint)
            continue

        try:
            # Pass 1: The Intent Classifier
            intent = parse_intent(user_input)
            
            # Placeholder for Mechanics Resolution (RollForge)
            rollforge_result = "Action parsed. No mechanic execution integrated in this pass."

            # Pass 2: The Storyteller prompt assembly
            prompt = prepare_storyteller_prompt(
                db_session,
                intent_summary=intent.get("intent_summary", "Unknown action"),
                rollforge_result=rollforge_result
            )
            
            # Note: For now, we echo the prompt. Once we wire up the real DB, 
            # we will send this prompt back to Ollama to generate the actual DM response.
            click.echo(prompt)

        except Exception as e:
            logger.error("Failed to process user input: %s", {"error": str(e)})
            click.echo("The DM seems confused by that action. Please try again.")

if __name__ == "__main__":
    cli()
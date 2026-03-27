import logging
import click
import ollama
from dotenv import load_dotenv

from myth_weaver.intent_parser import parse_intent
from myth_weaver.game_engine import handle_active_hint, prepare_storyteller_prompt
from myth_weaver.storyteller import generate_campaign_bible
from myth_weaver.database import get_db_session, DatabaseManager

logger = logging.getLogger(__name__)

# Load local environment variables for Postgres
load_dotenv()

@click.group()
def cli():
    """Myth Weaver: LLM Dungeon Master"""
    pass

@cli.command(name="start")
@click.option("--theme", default="Dark Fantasy", help="The theme of the campaign.")
def start_game(theme: str):
    """Start a new game session and generate the Campaign Bible."""
    click.echo(f"Initializing connection to PostgreSQL...")
    
    try:
        raw_session = get_db_session()
        db_manager = DatabaseManager(raw_session)
    except Exception as e:
        click.echo(f"Database connection failed. Is Docker running? Error: {e}")
        return

    click.echo(f"Generating the {theme} Campaign Bible. This may take a moment...")
    
    # Generate the campaign bible and retrieve the data
    campaign_data = generate_campaign_bible(theme, db_manager)
    # If successful, our DatabaseManager stub handles setting the campaign ID
    db_manager.campaign_id = 1 
    
    click.echo("\n" + "="*50)
    click.echo(f"Welcome to: {campaign_data.get('campaign_name', 'The Unknown Realm')}")
    click.echo("="*50 + "\n")
    click.echo(campaign_data.get('setting_description', 'A dark world awaits...'))
    click.echo("\nType '/hint' if you get stuck, or 'quit' to exit.\n")
    
    # The Interactive Game Loop
    while True:
        try:
            user_input = click.prompt("What do you do?", prompt_suffix="\n> ").strip()
        except (EOFError, click.exceptions.Abort):
            break
            
        if user_input.lower() in ["quit", "exit"]:
            click.echo("Ending session. Farewell, adventurer.")
            break
            
        if user_input.lower() == "/hint":
            logger.info("Player requested an active hint: %s", {"command": user_input})
            hint = handle_active_hint(db_manager)
            click.echo(f"\n[DM Hint]: {hint}\n")
            continue

        try:
            # Pass 1: Intent Classifier
            intent = parse_intent(user_input)
            rollforge_result = "Action parsed. Mechanics execution bypassed for this turn."

            # Pass 2: Prompt Assembly
            prompt = prepare_storyteller_prompt(
                db_manager,
                intent_summary=intent.get("intent_summary", "Unknown action"),
                rollforge_result=rollforge_result
            )
            
            # Pass 3: The Storyteller (Final Output)
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "system", "content": prompt}]
            )
            
            narrative = response.get("message", {}).get("content", "The DM stares at you blankly.")
            click.echo(f"\n{narrative}\n")

        except Exception as e:
            logger.error("Failed to process user input: %s", {"error": str(e)})
            click.echo("\nThe DM seems confused by that action. Please try again.\n")

if __name__ == "__main__":
    cli()
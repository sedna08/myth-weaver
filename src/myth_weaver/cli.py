import logging
import click
import ollama
from dotenv import load_dotenv

from myth_weaver.intent_parser import parse_intent
from myth_weaver.game_engine import handle_active_hint, prepare_storyteller_prompt
from myth_weaver.storyteller import generate_campaign_bible
from myth_weaver.database import get_db_session, DatabaseManager
from myth_weaver.models import Character # <-- NEW IMPORT

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
    
    campaign_data = generate_campaign_bible(theme, db_manager)
    
    # In a full implementation, generate_campaign_bible would return the ID.
    # For now, we assume this is the first campaign in a clean DB.
    db_manager.campaign_id = 1 
    
    # --- NEW MULTIPLAYER SETUP ---
    num_players = click.prompt("How many players are joining the adventure?", type=int, default=1)
    
    active_party = []
    for i in range(num_players):
        name = click.prompt(f"Enter name for Player {i+1}")
        desc = click.prompt(f"Enter background description for {name}")
        
        char = Character(
            campaign_id=db_manager.campaign_id,
            name=name,
            description=desc,
            hp=30,      # Default starting HP
            max_hp=30,  # Default starting Max HP
            armor_class=10,
            passive_perception=10
        )
        db_manager.add(char)
        active_party.append(name)
        
    db_manager.commit()
    # -----------------------------
    
    click.echo("\n" + "="*50)
    click.echo(f"Welcome to: {campaign_data.get('campaign_name', 'The Unknown Realm')}")
    click.echo("="*50 + "\n")
    click.echo(campaign_data.get('setting_description', 'A dark world awaits...'))
    click.echo("\nType '/hint' if you get stuck, or 'quit' to exit.\n")
    
    # --- UPDATED HOT-SEAT GAME LOOP ---
    turn_index = 0
    while True:
        try:
            current_player = active_party[turn_index % len(active_party)] if active_party else "Adventurer"
            user_input = click.prompt(f"{current_player}, what do you do?", prompt_suffix="\n> ").strip()
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
            # Add context to the intent summary so the LLM knows who is acting
            action_context = f"[{current_player} actions]: {user_input}"
            
            intent = parse_intent(action_context)
            rollforge_result = "Action parsed. Mechanics execution bypassed for this turn."

            prompt = prepare_storyteller_prompt(
                db_manager,
                intent_summary=intent.get("intent_summary", "Unknown action"),
                rollforge_result=rollforge_result
            )
            
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "system", "content": prompt}]
            )
            
            narrative = response.get("message", {}).get("content", "The DM stares at you blankly.")
            click.echo(f"\n{narrative}\n")
            
            # Advance to the next player's turn
            turn_index += 1

        except Exception as e:
            logger.error("Failed to process user input: %s", {"error": str(e)})
            click.echo("\nThe DM seems confused by that action. Please try again.\n")

@cli.command(name="load")
def load_game():
    """Load an existing campaign and resume playing."""
    try:
        raw_session = get_db_session()
        db_manager = DatabaseManager(raw_session)
    except Exception as e:
        click.echo(f"Database connection failed. Is Docker running? Error: {e}")
        return

    campaigns = db_manager.get_all_campaigns()
    
    if not campaigns:
        click.echo("No saved campaigns found. Use 'start' to create one.")
        return

    click.echo("\nAvailable Campaigns:")
    for idx, campaign in enumerate(campaigns):
        name = "Unknown"
        if campaign.campaign_bible:
             name = campaign.campaign_bible.get("campaign_name", "Unknown")
        click.echo(f"[{idx + 1}] {name} (Theme: {campaign.title})")

    # Get user selection
    selection = click.prompt("\nEnter the number of the campaign to load", type=int)
    
    if selection < 1 or selection > len(campaigns):
        click.echo("Invalid selection. Exiting.")
        return
        
    selected_campaign = campaigns[selection - 1]
    db_manager.campaign_id = selected_campaign.id
    
    campaign_name = "Unknown"
    if selected_campaign.campaign_bible:
        campaign_name = selected_campaign.campaign_bible.get("campaign_name", "Unknown")
        
    click.echo(f"\nResuming {campaign_name}...")
    
    # Rebuild the active party list for the hot-seat loop
    active_party = []
    characters = db_manager.session.query(Character).filter_by(campaign_id=db_manager.campaign_id).all()
    for char in characters:
        active_party.append(char.name)
        
    if not active_party:
         active_party.append("Adventurer") # Fallback if no characters exist
         
    # Fetch the last message to give the player context
    recent_history = db_manager.get_recent_history(db_manager.campaign_id, limit=1)
    if recent_history:
        click.echo("\n[DM's Last Message]:")
        click.echo(recent_history[0].content)

    click.echo("\nType '/hint' if you get stuck, or 'quit' to exit.\n")
    
    # --- HOT-SEAT GAME LOOP (Same as Start command) ---
    turn_index = 0
    while True:
        try:
            current_player = active_party[turn_index % len(active_party)]
            user_input = click.prompt(f"{current_player}, what do you do?", prompt_suffix="\n> ").strip()
        except (EOFError, click.exceptions.Abort):
            break
            
        if user_input.lower() in ["quit", "exit"]:
            click.echo("Ending session. Farewell, adventurer.")
            break
            
        if user_input.lower() == "/hint":
            hint = handle_active_hint(db_manager)
            click.echo(f"\n[DM Hint]: {hint}\n")
            continue

        try:
            action_context = f"[{current_player} actions]: {user_input}"
            intent = parse_intent(action_context)
            prompt = prepare_storyteller_prompt(
                db_manager,
                intent_summary=intent.get("intent_summary", "Unknown action"),
                rollforge_result="Action parsed. Mechanics execution bypassed for this turn."
            )
            
            response = ollama.chat(
                model="llama3",
                messages=[{"role": "system", "content": prompt}]
            )
            narrative = response.get("message", {}).get("content", "The DM stares at you blankly.")
            click.echo(f"\n{narrative}\n")
            turn_index += 1

        except Exception as e:
            logger.error("Failed to process user input: %s", {"error": str(e)})
            click.echo("\nThe DM seems confused by that action. Please try again.\n")
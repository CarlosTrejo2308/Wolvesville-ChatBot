import json
import os
from config import STATE_FILE

# Used to initialize state.json
DEFAULT_STATE = {
    "last_message_timestamp": None,
    "player_memory": {}
}

# Loads the state.json. If it doesnt exist, then it return default state
def load_state():
    """Load the bot state from disk or return a default state."""
    # If it doesnt exist, return default
    if not os.path.exists(STATE_FILE):
        return DEFAULT_STATE.copy()

    # Open the state file
    with open(STATE_FILE, "r") as f:
        content = f.read().strip()
    if not content: # No content, return default
        return DEFAULT_STATE.copy()

    # Return the content in state file
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return DEFAULT_STATE.copy()

def save_state(state):
    """Save the bot state to disk in JSON format."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def update_player_memory(state, player, fact):
    """Add a fact about a player to memory."""
    if player not in state["player_memory"]:
        state["player_memory"][player] = []
    if fact not in state["player_memory"][player]:
        state["player_memory"][player].append(fact)

def format_memory_for_prompt(player_memory):
    """Format stored player memory into a string for the LLM prompt."""
    if not player_memory:
        return "No player notes yet."
    lines = []
    for player, facts in player_memory.items():
        facts_str = "; ".join(facts)
        lines.append(f"- {player}: {facts_str}")
    return "\n".join(lines)
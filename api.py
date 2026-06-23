import requests
from config import CLAN_ID, WOLVESVILLE_TOKEN, API_BASE

HEADERS = {
    "Authorization": f"Bot {WOLVESVILLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_player_username(player_id):
    """Fetch a player's username from their ID. Falls back to the ID on error."""
    url = f"{API_BASE}/players/{player_id}"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        return response.json().get("username", player_id)
    except Exception:
        return player_id

def get_clan_chat():
    """Fetch recent clan chat messages."""
    url = f"{API_BASE}/clans/{CLAN_ID}/chat"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def send_clan_message(text):
    """Send a message to the clan chat."""
    url = f"{API_BASE}/clans/{CLAN_ID}/chat"
    response = requests.post(url, headers=HEADERS, json={"message": text})
    response.raise_for_status()
    print(f"[SENT] {text}")

def message_date(msg):
    """Return the timestamp string for a chat message."""
    return msg.get("date", "")

def message_text(msg):
    """Return the text of a chat message."""
    return msg.get("msg", "")

def message_username(msg, player_map=None):
    """Return the sender username for a chat message.

    Checks bot owner metadata first, then the resolved player_map,
    then falls back to inline playerUsername or the raw playerId.
    """
    if username := msg.get("playerBotOwnerUsername"):
        return username
    if player_map and (player_id := msg.get("playerId")):
        if resolved := player_map.get(player_id):
            return resolved
    if username := msg.get("playerUsername"):
        return username
    return msg.get("playerId", "unknown")

def is_skippable_message(msg, bot_owner_username=None):
    """Return True if a message should be ignored by the bot."""
    if msg.get("isSystem"):
        return True
    if not msg.get("msg"):
        return True
    if not msg.get("msg", "").lower().startswith("@wolfie"):
        return True
    if not msg.get("date"):
        return True
    if bot_owner_username and msg.get("playerBotOwnerUsername") == bot_owner_username:
        return True
    if bot_owner_username is None and "playerBotId" in msg:
        return True
    return False
import anthropic
from config import ANTHROPIC_API_KEY, SYSTEM_PROMPT_FILE
from storage import format_memory_for_prompt
from api import message_username, message_text
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

def load_system_prompt():
    """Read the system prompt text used for the LLM request."""
    with open(SYSTEM_PROMPT_FILE, "r") as f:
        return f.read()

def build_messages(new_messages, player_memory):
    """Build the messages array for the API call."""

    # Format chat as a readable block
    chat_block = "\n".join([
        f"{message_username(msg)}: {message_text(msg)}"
        for msg in new_messages
    ])
    memory_block = format_memory_for_prompt(player_memory)

    user_content = f"""
## Current player notes (what you remember about clan members)
{memory_block}

## New clan chat messages (reply to these)
{chat_block}

Reply naturally to the conversation above. Be concise.
If any message reveals something personal about a player worth remembering,
include it at the end in this exact format:
MEMORY: <username> | <fact>
You can include multiple MEMORY lines if needed.
"""
    return [{"role": "user", "content": user_content}]


def get_reply_and_extract_memory(new_messages, player_memory):
    """Call LLM, parse reply and any new memory facts."""

    system_prompt = load_system_prompt()
    messages = build_messages(new_messages, player_memory)

    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=200,
        system=system_prompt,
        messages=messages
    )

    raw = response.content[0].text.strip()

    # Split reply from memory lines
    reply_lines = []
    memory_updates = []  # list of (username, fact) tuples

    for line in raw.splitlines():
        if line.startswith("MEMORY:"):
            _, rest = line.split(":", 1)
            parts = rest.split("|")
            if len(parts) == 2:
                username = parts[0].strip()
                fact = parts[1].strip()
                memory_updates.append((username, fact))
        else:
            reply_lines.append(line)

    reply = "\n".join(reply_lines).strip()
    return reply, memory_updates
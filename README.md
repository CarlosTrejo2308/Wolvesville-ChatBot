# Wolvesville ChatBot

An AI-powered clan chat bot for [Wolvesville](https://www.wolvesville.com/). It polls your clan chat, replies with Claude, and remembers small facts about players over time.

Designed to run on a schedule (for example, every few minutes via cron or Task Scheduler), not as a always-on websocket server.

## How it works

Each run:

1. Fetches recent messages from the Wolvesville clan chat API
2. Filters to new text messages since the last run
3. Sends the conversation plus stored player notes to Claude
4. Posts a reply to clan chat
5. Saves the latest timestamp and any new player memories to disk

```text
main.py          Entry point — orchestrates the poll/reply loop
api.py           Wolvesville API client and message helpers
llm.py           Claude integration, reply + memory extraction
storage.py       Persistent state (timestamp + player memory)
config.py        Secrets and settings (not committed — see Setup)
data/
  system_prompt.md   Bot personality and clan context
  state.json         Runtime state (created/updated automatically)
```

## Prerequisites

- Python 3.10+
- A [Wolvesville bot token](https://docs.wolvesville.com/) with access to your clan chat
- An [Anthropic API key](https://console.anthropic.com/)

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/CarlosTrejo2308/Wolvesville-ChatBot
   cd Wolvesville-ChatBot
   ```

2. Install dependencies:

   ```bash
   pip install anthropic requests
   ```

3. Create `config.py` in the project root (this file is gitignored):

   ```python
   CLAN_ID = "your-clan-uuid"
   WOLVESVILLE_TOKEN = "your-wolvesville-bot-token"
   ANTHROPIC_API_KEY = "your-anthropic-api-key"

   API_BASE = "https://api.wolvesville.com"
   STATE_FILE = "data/state.json"
   SYSTEM_PROMPT_FILE = "data/system_prompt.md"
   BOT_OWNER_USERNAME = "BOT(YourUsername)"

   # Only reply to messages newer than this many seconds (first-run safety guard)
   MAX_MESSAGE_AGE_SECONDS = 60 * 60 * 24  # 24 hours
   ```

   | Variable | Description |
   | --- | --- |
   | `CLAN_ID` | UUID of your clan |
   | `WOLVESVILLE_TOKEN` | Bot token from the Wolvesville developer portal |
   | `ANTHROPIC_API_KEY` | Key for the Claude API |
   | `BOT_OWNER_USERNAME` | Your bot's `playerBotOwnerUsername` value (e.g. `BOT(YourUsername)`) — used to ignore the bot's own messages |
   | `MAX_MESSAGE_AGE_SECONDS` | On the first run, ignore messages older than this |

4. Customize the bot personality in `data/system_prompt.md`.

## Usage

Run manually:

```bash
python main.py
```

Schedule it to run periodically. Example cron entry (every 2 minutes):

```cron
*/2 * * * * cd /path/to/Wolvesville-ChatBot && python3 main.py
```

### Example output

```text
[FOUND] 3 new message(s)
  6f4a5326-8c8f-4d19-85ef-d20067086965: Hola clan
  8f16b52a-90dc-4b8d-8d0a-fa5f3a807db0: Quién juega hoy?
[MEMORY] 8f16b52a-90dc-4b8d-8d0a-fa5f3a807db0: Le gusta jugar por la noche
[SENT] ¡Yo me apunto! 🐺
```

If there is nothing new to process:

```text
No new messages since last run.
```

## Message filtering

The bot intentionally skips:

- Its own messages (`BOT_OWNER_USERNAME`)
- System messages (`isSystem: true`)
- Non-text entries (messages without a `msg` field, e.g. some special chat events)
- Messages already seen on a previous run
- Messages older than `MAX_MESSAGE_AGE_SECONDS` on the first run

## Player memory

Claude can append facts about players using lines like:

```text
MEMORY: CarlosTrejo2308 | Trabaja en oficina entre semana
```

These are parsed from the model response and stored in `data/state.json` under `player_memory`, then included in future prompts.

**Note:** The Wolvesville chat API often returns `playerId` instead of a display name for regular players. Memory keys may use IDs unless the API provides a username.

## Customization

- **Personality & clan lore:** edit `data/system_prompt.md`
- **Model / reply length:** edit `llm.py` (`model`, `max_tokens`)
- **Reset progress:** delete or edit `data/state.json` (set `last_message_timestamp` to `null` to reprocess recent messages within the age window)

## License

See [LICENSE](LICENSE).

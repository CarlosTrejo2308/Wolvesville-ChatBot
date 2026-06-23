from datetime import datetime, timezone
from api import (
    get_clan_chat,
    get_player_username,
    send_clan_message,
    message_date,
    message_text,
    message_username,
    is_skippable_message,
)
from llm import get_reply_and_extract_memory
from storage import load_state, save_state, update_player_memory
from config import MAX_MESSAGE_AGE_SECONDS, BOT_OWNER_USERNAME


def parse_timestamp(ts_string):
    """Parse ISO timestamp from API into a comparable datetime."""
    return datetime.fromisoformat(ts_string.replace("Z", "+00:00"))


def main():
    """Run the bot loop: fetch messages, build a reply, and update state."""
    state = load_state()
    last_ts = state["last_message_timestamp"]

    # 1. Fetch chat
    all_messages = get_clan_chat()
    if not all_messages:
        print("No messages in chat.")
        return

    # 2. Filter to new messages only
    new_messages = []
    for msg in all_messages:
        if is_skippable_message(msg, BOT_OWNER_USERNAME):
            continue

        msg_time = parse_timestamp(message_date(msg))
        msg_ts = message_date(msg)

        # Skip if older than last run
        if last_ts and msg_ts <= last_ts:
            continue

        # Skip if too old (first run safety guard)
        now = datetime.now(timezone.utc)
        age = (now - msg_time).total_seconds()
        if age > MAX_MESSAGE_AGE_SECONDS:
            continue

        new_messages.append(msg)

    if not new_messages:
        print("No new messages since last run.")
        # Still update timestamp to latest message
        dated_messages = [m for m in all_messages if message_date(m)]
        if dated_messages:
            latest = max(dated_messages, key=message_date)
            state["last_message_timestamp"] = message_date(latest)
            save_state(state)
        return

    # 3. Resolve player IDs to usernames
    unique_ids = {msg.get("playerId") for msg in new_messages if msg.get("playerId")}
    player_map = {pid: get_player_username(pid) for pid in unique_ids}

    print(f"[FOUND] {len(new_messages)} new message(s)")
    for m in new_messages:
        print(f"  {message_username(m, player_map)}: {message_text(m)}")

    # 4. Ask LLM for reply
    reply, memory_updates = get_reply_and_extract_memory(
        new_messages,
        state["player_memory"],
        player_map
    )

    # 5. Update player memory
    for username, fact in memory_updates:
        update_player_memory(state, username, fact)
        print(f"[MEMORY] {username}: {fact}")

    # 6. Send reply
    if reply:
        send_clan_message(reply)

    # 7. Save new timestamp (latest message seen)
    latest_ts = max(message_date(msg) for msg in new_messages)
    state["last_message_timestamp"] = latest_ts
    save_state(state)


if __name__ == "__main__":
    main()

import logging
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
from safety import is_injection_attempt
from config import MAX_MESSAGE_AGE_SECONDS, BOT_OWNER_USERNAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


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
        logging.info("No messages in chat.")
        return

    # 2. Filter to new @wolfie messages
    new_messages = []
    for msg in all_messages:
        if is_skippable_message(msg, BOT_OWNER_USERNAME):
            continue

        msg_time = parse_timestamp(message_date(msg))
        msg_ts = message_date(msg)

        if last_ts and msg_ts <= last_ts:
            continue

        now = datetime.now(timezone.utc)
        if (now - msg_time).total_seconds() > MAX_MESSAGE_AGE_SECONDS:
            continue

        new_messages.append(msg)

    if not new_messages:
        logging.info("No new messages since last run.")
        dated_messages = [m for m in all_messages if message_date(m)]
        if dated_messages:
            latest = max(dated_messages, key=message_date)
            state["last_message_timestamp"] = message_date(latest)
            save_state(state)
        return

    # 3. Resolve player IDs to usernames (with persistent cache)
    player_cache = state.setdefault("player_cache", {})
    unique_ids = {msg.get("playerId") for msg in new_messages if msg.get("playerId")}
    for pid in unique_ids:
        if pid not in player_cache:
            player_cache[pid] = get_player_username(pid)
    player_map = {pid: player_cache[pid] for pid in unique_ids}

    # 4. Drop injection attempts
    safe_messages = []
    for msg in new_messages:
        if is_injection_attempt(message_text(msg)):
            logging.warning(
                f"[SAFETY] Injection attempt from {message_username(msg, player_map)}: {message_text(msg)}"
            )
        else:
            safe_messages.append(msg)

    if not safe_messages:
        latest_ts = max(message_date(msg) for msg in new_messages)
        state["last_message_timestamp"] = latest_ts
        save_state(state)
        return

    logging.info(f"[FOUND] {len(safe_messages)} new message(s)")
    for m in safe_messages:
        logging.info(f"  {message_username(m, player_map)}: {message_text(m)}")

    # 5. Group by sender and reply to each individually
    messages_by_sender = {}
    for msg in safe_messages:
        sender = message_username(msg, player_map)
        messages_by_sender.setdefault(sender, []).append(msg)

    for sender_messages in messages_by_sender.values():
        reply, memory_updates = get_reply_and_extract_memory(
            sender_messages,
            state["player_memory"],
            player_map,
        )

        for username, fact in memory_updates:
            update_player_memory(state, username, fact)
            logging.info(f"[MEMORY] {username}: {fact}")

        if reply:
            send_clan_message(reply)

    # 6. Save state (timestamp, updated memory, player cache)
    latest_ts = max(message_date(msg) for msg in new_messages)
    state["last_message_timestamp"] = latest_ts
    save_state(state)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.error(f"Bot run failed: {e}")
        raise SystemExit(1)

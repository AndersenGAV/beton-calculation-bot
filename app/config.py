from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass(slots=True)
class Settings:
    bot_token: str
    allowed_user_ids: list[int]


def load_settings() -> Settings:
    load_dotenv()

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is empty. Fill it in the .env file.")

    raw_allowed_user_ids = os.getenv("ALLOWED_USER_IDS", "").strip()
    allowed_user_ids = [
        int(user_id.strip())
        for user_id in raw_allowed_user_ids.split(",")
        if user_id.strip()
    ]

    return Settings(
        bot_token=bot_token,
        allowed_user_ids=allowed_user_ids,
    )

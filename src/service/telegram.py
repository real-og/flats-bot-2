from src.shared.config import proxy, required
from src.shared.http import request_json, HTTPFailure
from src.shared.observability import redact


class TelegramFailure(Exception):
    def __init__(self, code, description, retry_after=None):
        self.code = code
        self.retry_after = retry_after
        super().__init__(redact(f"Telegram {code}: {description}")[:500])


def call(method, payload):
    token = required("BOT_TOKEN")
    try:
        result = request_json(
            f"https://api.telegram.org/bot{token}/{method}", payload, proxy=proxy()
        )
    except HTTPFailure as exc:
        result = exc.body if isinstance(exc.body, dict) else {}
        raise TelegramFailure(
            exc.status,
            result.get("description", "HTTP error"),
            result.get("parameters", {}).get("retry_after"),
        ) from None
    if not isinstance(result, dict) or not result.get("ok"):
        result = result if isinstance(result, dict) else {}
        raise TelegramFailure(
            result.get("error_code", 502),
            result.get("description", "Invalid API response"),
            result.get("parameters", {}).get("retry_after"),
        )
    return result["result"]


def send_ad(chat_id, ad):
    caption = ad.create_telegram_caption()
    photos = ad.photos[:10]
    # Very long captions use a single text message rather than a partial send.
    if len(caption) > 1000:
        photos = []
    try:
        if len(photos) > 1:
            media = [{"type": "photo", "media": p} for p in photos]
            media[0].update(caption=caption, parse_mode="HTML")
            return call("sendMediaGroup", {"chat_id": chat_id, "media": media})
        if photos:
            return call(
                "sendPhoto",
                {
                    "chat_id": chat_id,
                    "photo": photos[0],
                    "caption": caption,
                    "parse_mode": "HTML",
                },
            )
    except TelegramFailure as exc:
        if exc.code != 400:
            raise
        # Explicit rejection of media: safely degrade to the listing link/text.
    return call(
        "sendMessage", {"chat_id": chat_id, "text": caption, "parse_mode": "HTML"}
    )

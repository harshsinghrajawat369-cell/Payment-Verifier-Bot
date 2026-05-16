import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pytgcalls import PyTgCalls
from pytgcalls.types import MediaStream
from pytgcalls.types.stream import AudioPiped, StreamAudioEnded
from yt_dlp import YoutubeDL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("musicbot")

API_ID = int(os.getenv("38074255", "0"))
API_HASH = os.getenv("b24d8bf27bba4316a37c4bf2a7e9b9cf", "")
BOT_TOKEN = os.getenv("8612587267:AAHm6rkGfZdvrHCd6NZJNP3vfQ4VD24rd0I", "")
OWNER_ID = int(os.getenv("7513729138", "0"))

if not API_ID or not API_HASH or not BOT_TOKEN:
    raise RuntimeError("Please set API_ID, API_HASH, BOT_TOKEN environment variables")

app = Client("music_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
vc = PyTgCalls(app)


@dataclass
class Track:
    title: str
    url: str
    source_url: str
    requested_by: str


queues: Dict[int, List[Track]] = {}
now_playing: Dict[int, Track] = {}


def controls_keyboard(chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("⏭️ Skip", callback_data=f"skip:{chat_id}"),
                InlineKeyboardButton("⏸️ Pause", callback_data=f"pause:{chat_id}"),
                InlineKeyboardButton("▶️ Resume", callback_data=f"resume:{chat_id}"),
                InlineKeyboardButton("⏹️ Stop", callback_data=f"stop:{chat_id}"),
            ],
            [
                InlineKeyboardButton("🎧 Live Playback", callback_data=f"now:{chat_id}"),
                InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/KSHATRIYA_OP"),
            ],
        ]
    )


def extract_audio(query: str) -> Optional[Track]:
    ydl_opts = {
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(f"ytsearch1:{query}", download=False)
        if not info or "entries" not in info or not info["entries"]:
            return None
        entry = info["entries"][0]
        return Track(
            title=entry.get("title", "Unknown title"),
            url=entry.get("url", ""),
            source_url=entry.get("webpage_url", ""),
            requested_by="Unknown",
        )


async def play_next(chat_id: int):
    queue = queues.get(chat_id, [])
    if not queue:
        now_playing.pop(chat_id, None)
        return
    track = queue.pop(0)
    now_playing[chat_id] = track
    await vc.change_stream(chat_id, AudioPiped(track.source_url))


@app.on_message(filters.command("start") & filters.private)
async def start_cmd(_, message: Message):
    await message.reply_text(
        "✨ 𝖶𝖾𝗅𝖼𝗈𝗆𝖾 𝗍𝗈 𝗍𝗁𝖾 𝖥𝗎𝗍𝗎𝗋𝗂𝗌𝗍𝗂𝖼 𝖬𝗎𝗌𝗂𝖼 𝖡𝗈𝗍!\n\n"
        "🎵 Add me to your group and promote me as admin.\n"
        "🎬 I can play music + YouTube audio in voice chat.\n"
        "⚡ Commands: /play /skip /pause /resume /stop /queue",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("👨‍💻 Developer", url="https://t.me/your_username")]]
        ),
    )


@app.on_message(filters.command("play") & filters.group)
async def play_cmd(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text("❌ Give me a song name. Example: /play Faded Alan Walker")

    query = " ".join(message.command[1:])
    status = await message.reply_text("🔎 Searching...")

    track = await asyncio.to_thread(extract_audio, query)
    if not track:
        return await status.edit_text("❌ Song not found.")

    track.requested_by = message.from_user.mention if message.from_user else "Anonymous"
    chat_id = message.chat.id
    queues.setdefault(chat_id, []).append(track)

    if chat_id not in now_playing:
        await vc.join_group_call(chat_id, AudioPiped(track.source_url))
        now_playing[chat_id] = queues[chat_id].pop(0)
        await status.edit_text(
            f"🎵 Now Playing: **{track.title}**\n👤 Requested by: {track.requested_by}",
            reply_markup=controls_keyboard(chat_id),
        )
    else:
        await status.edit_text(
            f"✅ Added to queue: **{track.title}**\n📌 Position: {len(queues[chat_id])}",
            reply_markup=controls_keyboard(chat_id),
        )


@app.on_message(filters.command("queue") & filters.group)
async def queue_cmd(_, message: Message):
    chat_id = message.chat.id
    current = now_playing.get(chat_id)
    q = queues.get(chat_id, [])
    if not current and not q:
        return await message.reply_text("📭 Queue is empty.")

    text = ["🎶 **Live Queue**"]
    if current:
        text.append(f"\n▶️ Now: {current.title}")
    if q:
        for i, t in enumerate(q[:15], start=1):
            text.append(f"{i}. {t.title}")
    await message.reply_text("\n".join(text), reply_markup=controls_keyboard(chat_id))


@app.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(_, message: Message):
    if not message.from_user or message.from_user.id != OWNER_ID:
        return
    if len(message.command) < 2:
        return await message.reply_text("Usage: /broadcast your message")

    text = message.text.split(maxsplit=1)[1]
    sent = 0
    async for dialog in app.get_dialogs():
        try:
            if dialog.chat.type in ("group", "supergroup"):
                await app.send_message(dialog.chat.id, f"📢 {text}")
                sent += 1
        except Exception:
            continue
    await message.reply_text(f"✅ Broadcast sent to {sent} chats")


@app.on_callback_query()
async def cb_handler(_, cb):
    action, cid = cb.data.split(":", maxsplit=1)
    chat_id = int(cid)

    if action == "skip":
        await play_next(chat_id)
        await cb.answer("Skipped")
    elif action == "pause":
        await vc.pause_stream(chat_id)
        await cb.answer("Paused")
    elif action == "resume":
        await vc.resume_stream(chat_id)
        await cb.answer("Resumed")
    elif action == "stop":
        queues[chat_id] = []
        now_playing.pop(chat_id, None)
        await vc.leave_group_call(chat_id)
        await cb.answer("Stopped")
    elif action == "now":
        current = now_playing.get(chat_id)
        await cb.answer(current.title if current else "Nothing is playing", show_alert=True)


@vc.on_stream_end()
async def on_stream_end(_, update: StreamAudioEnded):
    await play_next(update.chat_id)


async def main():
    await app.start()
    await vc.start()
    logger.info("Bot started")
    await idle()


from pyrogram.idle import idle

if __name__ == "__main__":
    app.run()


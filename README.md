# Telegram Group Music Bot

A feature-rich Telegram group music bot with queue, inline controls, owner broadcast, and voice chat playback.

## Features
- Owner command: `/broadcast`
- Playback commands: `/play`, `/queue`
- Inline control buttons: Skip, Pause, Resume, Stop
- Live playback status button
- Developer button on bot messages

## Setup
1. Create a bot from BotFather.
2. Create Telegram API credentials from my.telegram.org.
3. Copy `.env.example` to `.env` and fill values.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Run bot:
   ```bash
   python bot.py
   ```

## Notes
- Promote the bot as admin in your group.
- Voice chat should be active in group.
- The bot currently uses YouTube search/audio extraction via `yt-dlp`.

import os
import discord
from flask import Flask, Response
from threading import Thread

# Discord Bot設定
TOKEN = os.environ["BOT_TOKEN"]
LIST_CHANNEL_ID = int(os.environ["LIST_CHANNEL_ID"])

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)
participants = []
list_message = None

@client.event
async def on_ready():
    print(f"Bot起動: {client.user}")

@client.event
async def on_message(message):
    global list_message
    if message.author.bot:
        return

    text = message.content.strip()
    author_name = message.author.display_name
    channel = message.guild.get_channel(LIST_CHANNEL_ID)

    if text == "参加希望":
        if author_name not in participants:
            participants.append(author_name)
            await update_list(channel)
    elif text == "参加辞退":
        if author_name in participants:
            participants.remove(author_name)
            await update_list(channel)
    elif text.endswith("参加辞退") and message.mentions:
        for user in message.mentions:
            name = user.display_name
            if name in participants:
                participants.remove(name)
        await update_list(channel)
    elif text == "リストを初期化":
        participants.clear()
        await update_list(channel)

async def update_list(channel):
    global list_message
    if participants:
        content = "【参加者リスト】\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(participants))
    else:
        content = "【参加者リスト】\nまだ誰もいません"

    if list_message is None:
        list_message = await channel.send(content)
    else:
        await list_message.edit(content=content)

# FlaskでPing用サーバー
app = Flask("")

@app.route("/")
def home():
    return Response("OK", status=200)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

flask_thread = Thread(target=run_flask)
flask_thread.start()

# Discord Bot起動
client.run(TOKEN)

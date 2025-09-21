import os
import discord
from discord.ext import commands
from discord.ui import View, Button
from flask import Flask, Response
from threading import Thread

# ==============================
# Discord Bot
# ==============================
TOKEN = os.environ["BOT_TOKEN"]
LIST_CHANNEL_ID = int(os.environ["LIST_CHANNEL_ID"])
ADMIN_ROLE_ID = int(os.environ["SERVER_MANAGER_ID"])  # 管理者ロールIDに変更

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

participants = []
list_message = None


class ParticipantView(View):
    def __init__(self):
        super().__init__(timeout=None)
        for name in participants:
            self.add_item(RemoveButton(name))


class RemoveButton(Button):
    def __init__(self, name):
        super().__init__(label=f"❌ {name}", style=discord.ButtonStyle.danger)
        self.name = name

    async def callback(self, interaction: discord.Interaction):
        # 管理者ロールをIDで確認
        if not any(role.id == ADMIN_ROLE_ID for role in interaction.user.roles):
            await interaction.response.send_message("⚠️ この操作は管理者のみ可能です。", ephemeral=True)
            return

        if self.name in participants:
            participants.remove(self.name)
            await interaction.response.send_message(f"{self.name} を削除しました。", ephemeral=True)

            channel = interaction.guild.get_channel(LIST_CHANNEL_ID)
            await update_list(channel)
        else:
            await interaction.response.send_message("既に削除済みです。", ephemeral=True)


@bot.event
async def on_ready():
    print(f"Bot起動: {bot.user}")


@bot.event
async def on_message(message):
    global participants
    if message.author.bot:
        return

    text = message.content.strip()
    author_name = message.author.display_name
    channel = message.guild.get_channel(LIST_CHANNEL_ID)

    # ---- 自分が参加希望 ----
    if text == "参加希望":
        if author_name not in participants:
            participants.append(author_name)
            await update_list(channel)

    # ---- 自分が参加辞退 ----
    elif text == "参加辞退":
        if author_name in participants:
            participants.remove(author_name)
            await update_list(channel)

    # ---- 他人を辞退させる（@〇〇 参加辞退）----
    elif text.endswith("参加辞退") and message.mentions:
        for user in message.mentions:
            name = user.display_name
            if name in participants:
                participants.remove(name)
        await update_list(channel)

    # ---- 他人を参加希望にする（@〇〇 参加希望）----
    elif text.endswith("参加希望") and message.mentions:
        for user in message.mentions:
            name = user.display_name
            if name not in participants:
                participants.append(name)
        await update_list(channel)

    # ---- リスト初期化 ----
    elif text == "リストを初期化":
        if any(role.id == ADMIN_ROLE_ID for role in message.author.roles):
            participants.clear()
            await update_list(channel)
        else:
            await message.channel.send("⚠️ リスト初期化は管理者のみ可能です。")


async def update_list(channel):
    global list_message
    if participants:
        content = "【参加者リスト】\n" + "\n".join(f"{i+1}. {name}" for i, name in enumerate(participants))
        view = ParticipantView()
    else:
        content = "【参加者リスト】\nまだ誰もいません"
        view = None

    try:
        if list_message:
            await list_message.edit(content=content, view=view)
        else:
            list_message = await channel.send(content, view=view)
    except discord.NotFound:
        # 既存メッセージが削除されていた場合は新規送信
        list_message = await channel.send(content, view=view)


# ==============================
# Ping用Webサーバー（Flask）
# ==============================
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
bot.run(TOKEN)

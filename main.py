import discord
from discord.ext import commands

import psycopg2

import os
from datetime import datetime, timedelta

from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

DATABASE_URL = os.getenv("DATABASE_URL")


conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)



async def import_history():

    after = datetime.now() - timedelta(days=14)

    print("過去ログ取得開始")

    for guild in bot.guilds:

        print(f"サーバー: {guild.name}")

        for channel in guild.text_channels:

            try:

                print(f"取得中: #{channel.name}")

                count = 0

                async for msg in channel.history(
                    limit=None,
                    after=after
                ):

                    if msg.author.bot:
                        continue

                    cur.execute(
                        """
                        INSERT INTO messages
                        (
                        id,
                        guild_id,
                        guild_name,
                        channel_id,
                        channel_name,
                        author_id,
                        author_name,
                        content,
                        message_created_at,
                        reply_to
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO NOTHING
                        """,
                        (
                        msg.id,
                        msg.guild.id,
                        msg.guild.name,
                        msg.channel.id,
                        msg.channel.name,
                        msg.author.id,
                        str(msg.author),
                        msg.content,
                        msg.created_at,
                        (
                                msg.reference.message_id
                                if msg.reference
                                else None
                        )
                        )
                    )
                    count += 1

                conn.commit()

                print(
                    f"完了 #{channel.name} "
                    f"{count}件"
                )

            except Exception as e:

                print(
                    f"失敗 #{channel.name}"
                )

                print(e)

    print("過去ログ取得完了")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await import_history()

@bot.event
async def on_message(message):

    # DM無視
    if message.guild is None:
        return

    # Bot無視
    if message.author.bot:
        return

    print(
        f"[{message.guild.name}] "
        f"#{message.channel.name} "
        f"{message.author}: "
        f"{message.content}"
    )

    cur.execute(
        """
        INSERT INTO messages
        (
        id,
        guild_id,
        guild_name,
        channel_id,
        channel_name,
        author_id,
        author_name,
        content,
        message_created_at,
        reply_to
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING
        """,
        (
        message.id,
        message.guild.id,
        message.guild.name,
        message.channel.id,
        message.channel.name,
        message.author.id,
        str(message.author),
        message.content,
        message.created_at,
        (
            message.reference.message_id
            if message.reference
            else None
        )
        )
    )

    conn.commit()

    await bot.process_commands(message)


bot.run(TOKEN)
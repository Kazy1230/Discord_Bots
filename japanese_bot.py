import re
import os
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from models import SessionLocal, UserStat
from datetime import datetime, timedelta, UTC, time
from sqlalchemy import func
from zoneinfo import ZoneInfo
import json
import random

load_dotenv()

with open("jp_quiz_db.json","r",encoding="utf-8") as f:
    data = json.load(f)

TOKEN = os.getenv("JP_DISCORD_TOKEN")
STUDY_RECORD_CHANNEL = int(os.getenv("JP_STUDY_RECORD_CHANNEL"))
QUIZ_CHANNEL = int(os.getenv("JP_QUIZ_CHANNEL"))

JST = ZoneInfo("Asia/Tokyo")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

def current_hour():
    now = datetime.now(UTC)
    return now.replace(minute=0, second=0,microsecond=0)

def get_daily_ranking():
    day_ago = current_hour() - timedelta(days=1)
    end = current_hour()
    session = SessionLocal()
    
    ranking = (
        session.query(
            UserStat.user_id,
            func.sum(UserStat.amount).label("total")
        )
        .filter(UserStat.created_at >= day_ago)
        .filter(UserStat.created_at < end)
        .filter(UserStat.server == "JP")
        .group_by(UserStat.user_id)
        .order_by(func.sum(UserStat.amount).desc())
        .limit(1)
        .all()
    )
    session.close()
    return ranking
    
async def send_daily_ranking():
    ranking = get_daily_ranking()
    study_record_channel_bot = bot.get_channel(STUDY_RECORD_CHANNEL)
    quiz_channel_bot = bot.get_channel(QUIZ_CHANNEL)
    if ranking:
        user_id, total = ranking[0]
        await study_record_channel_bot.send(f"🏆 今日の1位: <@{user_id}> - {total}")
    else:
        await study_record_channel_bot.send("まだデータがありません。")

    return


def get_weekly_ranking():
    seven_days_ago = current_hour() - timedelta(days=7)
    end = current_hour()
    session = SessionLocal()
    
    ranking = (
        session.query(
            UserStat.user_id,
            func.sum(UserStat.amount).label("total")
        )
        .filter(UserStat.created_at >= seven_days_ago)
        .filter(UserStat.created_at < end)
        .filter(UserStat.server == "JP")
        .group_by(UserStat.user_id)
        .order_by(func.sum(UserStat.amount).desc())
        .limit(3)
        .all()
    )
    session.close()
    return ranking
    
async def send_weekly_ranking():
    ranking = get_weekly_ranking()
    study_record_channel_bot = bot.get_channel(STUDY_RECORD_CHANNEL)
    quiz_channel_bot = bot.get_channel(QUIZ_CHANNEL)
    if ranking:
        text = "🏆 週間ランキング\n"
        medals = ["🥇", "🥈", "🥉"]

        for i, (user_id, total) in enumerate(ranking):
            text += f"{medals[i]} <@{user_id}> - {total}\n"

        await study_record_channel_bot.send(text)

    else:
        await study_record_channel_bot.send("今週のデータはありません。")

    return

def reset_all_scores():
    session = SessionLocal()
    session.query(UserStat).delete()
    session.commit()
    session.close()
    return

async def send_quiz(content="general"):
    quiz_channel_bot = bot.get_channel(QUIZ_CHANNEL)
    item = random.choice(data)
    
    if content =="!n2":
        while item['level'] != 2:
            item = random.choice(data)
    elif content =="!n3":
        while item['level'] != 3:
            item = random.choice(data)
    elif content =="!n4":
        while item['level'] != 4:
            item = random.choice(data)
    elif content =="!n5":
        while item['level'] != 5:
            item = random.choice(data)
    elif content =="!n1":
        while item['level'] != 1:
            item = random.choice(data)
    
    meaning_text = "\n".join([f"{exp['expression']} = ||{exp['meaning']}||" for exp in item['expressions']])
    embed = discord.Embed(
        title = f"📘 Lv.N{item['level']}",
        color = 0x2b6cb0
        )
    
    embed.add_field(
        name = "✒ Sentence",
        value = f"*{item['sentence']}*",
        inline = False
        )
    
    embed.add_field(
        name = "🔄Translation",
        value = item['translation'],
        inline = False
        )
    
    embed.add_field(
        name = "💡 Meaning",
        value = meaning_text,
        inline = False
        )
    chosen_item = random.choice(item['expressions'])
    embed.add_field(
        name = "🧠 Nuance",
        value = f"{chosen_item['expression']} : {chosen_item['nuance']}",
        inline = False
        )
    
    print("send")
    await quiz_channel_bot.send(embed=embed)
    print("sent")
    return

# 🔢 数字検知 & 累積処理
@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if message.channel.id == STUDY_RECORD_CHANNEL:
        if message.content.startswith("!daily"):
            await send_daily_ranking()

        if message.content.startswith("!weekly"):
            await send_weekly_ranking()

        if message.content.startswith("!reset"):
            await reset_all_scores()
            await message.channel.send("全てのデータを削除しました")

        numbers = re.findall(r"\d+", message.content)

        if numbers:
            total_add = sum(int(n) for n in numbers)

            db = SessionLocal()
            try:
                log = UserStat(
                    user_id=str(message.author.id),
                    amount=total_add,
                    created_at=current_hour(),
                    server="JP"
                )
                
                db.add(log)
                db.commit()

                await message.add_reaction("✅")

            finally:
                db.close()
    elif message.channel.id == QUIZ_CHANNEL:
        if message.content.startswith("!quiz"):
            await send_quiz("general")
        elif message.content.startswith("!n2") or message.content.startswith("!n3") or message.content.startswith("!n4") or message.content.startswith("!n5"):
            await send_quiz(message.content)
    else:
        return
        

    await bot.process_commands(message)

@tasks.loop(time=time(hour=8,minute=0,tzinfo=JST))
async def daily_scheduler():
    now_utc = datetime.now(UTC)
    now_jst = now_utc.astimezone(JST)
    if now_jst.weekday() == 6:
        await send_weekly_ranking()
        await send_quiz()
    else:
        await send_daily_ranking()
        await send_quiz()

@bot.event
async def on_ready():
    daily_scheduler.start()




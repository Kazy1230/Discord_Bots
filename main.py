import asyncio
from english_bot import bot as en_bot, TOKEN as EN_TOKEN
from japanese_bot import bot as jp_bot, TOKEN as JP_TOKEN

async def start_bots():
    # 二つのボットを同時に起動タスクとして登録
    await asyncio.gather(
        en_bot.start(EN_TOKEN),
        jp_bot.start(JP_TOKEN)
    )

if __name__ == "__main__":
    #try:
    asyncio.run(start_bots())
    #except KeyboardInterrupt:
        # 終了時のエラーハンドリング
        #pass
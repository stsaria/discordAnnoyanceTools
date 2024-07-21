import traceback, requests, datetime, time

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
        for i in range(numberOfExecutions):
            if logId in stops:
                logs.pop(logId)
                return
            logs[logId] += f"{str(datetime.datetime.now())} Send WebhookNuke - "
            try:
                response = self.send(message)
                if response.status_code == 204:
                    logs[logId] += "Success"
                else:
                    logs[logId] += f"Failed({response.status_code})"
            except:
                print(traceback.format_exc())
                logs[logId] += "Failed(Exception)"
            logs[logId] += "\n"
            time.sleep(latency*0.001)
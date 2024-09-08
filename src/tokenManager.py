import json, os

class TokenManager:
    data = {"tokens":[]}
    def __init__(self, fileName:str):
        self.fileName = fileName
        if os.path.isfile(fileName):
            with open(fileName, encoding="utf-8") as f:
                self.data = json.load(f)
        else:
            with open(fileName, encoding="utf-8", mode="w") as f:
                json.dump(self.data, f)
    def saveData(self):
        with open(self.fileName, encoding="utf-8", mode="w") as f:
            json.dump(self.data, f)
    def getTokenInfos(self):
        return self.data["tokens"]
    def addToken(self, token:str, email:str, password:str, etc:str, save=True):
        self.data["tokens"].append({"token":token, "email":email, "password":password, "etc":etc})
        if save: self.saveData()
    def editToken(self, n:int, token:str, email:str, password:str, etc:str, save=True):
        self.data["tokens"][n] = {"token":token, "email":email, "password":password, "etc":etc}
        if save: self.saveData()
    def deleteToken(self, x:int|dict, save=True):
        if type(x) == int:
            self.data["tokens"].pop(x)
        elif type(x) == dict:
            self.data["tokens"].remove(x)
        if save: self.saveData()
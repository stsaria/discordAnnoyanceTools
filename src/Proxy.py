import requests, os

class Proxy:
    def __init__(self, fileName:str) -> None:
        self.fileName = fileName
    def checkProxy(self, proxy:str, testUrl="https://google.com", timeout=10):
        try:
            requests.get(testUrl, proxies={
                "http": proxy,
                "https": proxy
            }, timeout=timeout)
            return True
        except:
            return False
    def setProxy(self, proxy:str):
        if not self.checkProxy(proxy):
            return False
        os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = proxy
        with open(self.fileName, mode="w") as f:
            f.write(proxy)
        return True
    def getProxy(self):
        if not os.path.isfile(self.fileName):
            return None
        with open(self.fileName, mode="r") as f:
            proxy = f.read()
            if not self.checkProxy(proxy):
                return None
            os.environ['HTTP_PROXY'] = os.environ['HTTPS_PROXY'] = proxy
            return proxy
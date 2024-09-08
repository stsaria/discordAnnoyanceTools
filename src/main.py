import subprocess, webbrowser, endpoints, platform, shutil, sys, os

def main():
    windowsCmds = f"""pythonExec -m venv selfBot
cmd /c .\\selfBot\\Scripts\\activate.bat
.\\selfBot\\Scripts\\pip.exe install -r requirementsSelfBot.txt
.\\selfBot\\Scripts\\python.exe src/selfDiscordBot.py"""
    unixCmds = f"""pythonExec -m venv selfBot
bash ./selfBot/bin/activate
./selfBot/bin/pip install -r requirementsSelfBot.txt
./selfBot/bin/python src/selfDiscordBot.py"""

    if platform.system() == "Windows":
        cmds = windowsCmds
    else:
        cmds = unixCmds
    
    cmds = cmds.split("\n")
    for cmd in cmds:
        cmd = cmd.split(" ")
        if cmd[0] == "pythonExec":
            cmd[0] = sys.executable
        while True:
            if os.path.isfile(cmd[0]) or shutil.which(cmd[0]):
                break
        if cmd == cmds[1].split(" "):
            subprocess.run(" ".join(cmd), shell=True)
        else:
            p = subprocess.Popen(cmd)
        if not cmd == cmds[-1].split(" "):
            p.communicate()
    
    port = 8080
    webbrowser.open(f"http://localhost:{port}")
    endpoints.app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
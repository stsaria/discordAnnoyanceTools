import subprocess, webbrowser, endpoints, platform, sys

def main():
    windowsCmds = f"""pythonExec -m venv selfBot
cmd /c .\\selfBot\\Scripts\\activate.bat
.\\selfBot\\Scripts\\pip.exe install -r requirementsSelfBot.txt
.\\selfBot\\Scripts\\python.exe src/selfDiscordBot.py"""
    unixCmds = f"""pythonExec -m venv selfBot
./selfBot/bin/activate
./selfBot/bin/pip install -r requirementsSelfBot.txt
./selfBot/bin/python.exe src/selfDiscordBot.py"""

    if platform.system() == "Windows":
        cmds = windowsCmds
    else:
        cmds = unixCmds
    
    cmds = cmds.split("\n")
    for cmd in cmds:
        cmd = cmd.split(" ")
        if cmd[0] == "pythonExec":
            cmd[0] = sys.executable
        p = subprocess.Popen(cmd)
        if not cmd == cmds[-1].split(" "):
            p.communicate()
        else:
            print(2)
    
    port = 8080
    webbrowser.open(f"http://localhost:{port}")
    endpoints.app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
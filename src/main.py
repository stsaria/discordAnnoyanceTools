import webbrowser, endpoints, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    port = 8080
    if sys.argv[-1].isdecimal():
        port = int(sys.argv[-1])
    webbrowser.open(f"http://127.0.0.1:{port}")
    endpoints.app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
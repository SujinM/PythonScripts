import subprocess, sys, time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class Restart(FileSystemEventHandler):
    def __init__(self):
        self.proc = self._start()
    def _start(self):
        return subprocess.Popen([sys.executable, "app.py"])
    def on_modified(self, event):
        if event.src_path.endswith(".py"):
            print(f"Change detected: {event.src_path} — restarting...")
            self.proc.kill()
            time.sleep(0.3)
            self.proc = self._start()

handler = Restart()
obs = Observer()
obs.schedule(handler, path="src", recursive=True)
obs.start()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    obs.stop()
    handler.proc.kill()
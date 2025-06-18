from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from signal import pause

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, file_path, callback):
        self.file_path = file_path
        self.callback = callback

    def on_modified(self, event):
        if event.src_path.endswith(self.file_path):
            self.callback
            print("self.file_path")

observer = Observer()
observer.schedule(FileChangeHandler(), path=".", recursive=False)
observer.start()

try:
    while True:
        pause()
        # pass  # 保持运行
except KeyboardInterrupt:
    observer.stop()
observer.join()
import argparse
import os
import runpy
import sys
import threading
import time
import traceback
from datetime import datetime
from datetime import timedelta
from multiprocessing import Queue
from types import ModuleType

from StreamDeck.Transport.Transport import TransportError

from sleuthdeck.deck import Deck
from watchdog.events import FileSystemEventHandler


class ReloadingHandler(FileSystemEventHandler):
    def __init__(self, script: str):
        if not os.path.exists(script):
            raise ValueError(f"Missing script file {script}")
        self.deck = None
        self.script = script
        self._run_thread = threading.Thread(target=self.run)
        self._reloading_queue = Queue()
        self._run_thread.start()
        self._last_modified = datetime.now()

    def on_modified(self, event):
        now = datetime.now()
        if now - self._last_modified < timedelta(milliseconds=500):
            return

        self._last_modified = now
        self._reloading_queue.put(object())

    def run(self):
        mod_name = self.script.replace("/", ".")
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        try:
            while not self.deck or self._reloading_queue.get():
                print(f"Running {mod_name}")
                try:
                    mod = runpy.run_module(mod_name)
                    print("done running")
                except:
                    print(f"Error loading script")
                    traceback.print_exc()
                    continue

                if "run" not in mod:
                    raise ValueError(f"Script {self.script} missing 'run' function")

                if self.deck:
                    print("Closing old deck")
                    self.deck.close()
                try:
                    deck = Deck()
                except (RuntimeError, TransportError):
                    print("No streamdeck found, waiting 5s")
                    time.sleep(5)
                    self.deck = None
                    continue

                print(f"Loaded new deck from {self.script}")
                self.deck = deck
                try:
                    mod["run"](deck)
                except Exception as e:
                    print(f"Error: {e}")
                    traceback.print_exc()
                    self.deck = None
                    continue
                while self.deck.stream_deck.is_open() and self._reloading_queue.empty():
                    time.sleep(1)

                if not self.deck.stream_deck.is_open():
                    print("Closing deck")
                    self.deck = None

        except EOFError:
            if self.deck and self.deck.stream_deck.is_open():
                self.deck.close()

        print("Exiting")

    def stop(self):
        self._reloading_queue.close()

    def on_created(self, event):
        self._reloading_queue.put(object())

    def on_deleted(self, event):
        self.stop()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Python script")
    parser.add_argument("script", metavar="SCRIPT", help="Path to the script to run")
    opts = parser.parse_args()

    from watchdog.observers import Observer

    event_handler = ReloadingHandler(opts.script)
    observer = Observer()
    observer.schedule(event_handler, path=opts.script)
    observer.start()
    # event_handler.on_created(None)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        event_handler.stop()
        observer.stop()
    observer.join()

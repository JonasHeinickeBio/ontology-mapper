"""
Loading bar utilities for long-running operations.
"""

import threading
import time


class LoadingBar:
    """Simple animated loading bar for long operations"""

    def __init__(self, message: str = "Loading", style: str = "dots"):
        self.message = message
        self.style = style
        self.running = False
        self.thread: threading.Thread | None = None
        self.styles = {
            "dots": ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"],
            "spinner": ["|", "/", "-", "\\"],
            "bar": ["▱", "▰"],
            "pulse": ["🔍", "🔎"],
        }

    def _animate(self):
        """Internal animation loop"""
        frames = self.styles.get(self.style, self.styles["dots"])
        frame_count = len(frames)
        i = 0

        while self.running:
            if self.style == "bar":
                # Progress bar style
                bar_length = 20
                filled = i % bar_length
                bar = "█" * filled + "░" * (bar_length - filled)
                print(f"\r{self.message} [{bar}]", end="", flush=True)
            else:
                # Spinner style
                frame = frames[i % frame_count]
                print(f"\r{frame} {self.message}...", end="", flush=True)

            time.sleep(0.1)
            i += 1

    def start(self):
        """Start the loading animation"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._animate)
            self.thread.daemon = True
            self.thread.start()

    def stop(self):
        """Stop the loading animation"""
        if self.running:
            self.running = False
            if self.thread:
                self.thread.join()
            print("\r" + " " * 50, end="")  # Clear the line
            print("\r", end="", flush=True)

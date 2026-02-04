"""Chrome browser process manager for CDP connection."""

import os
import signal
import subprocess
import time
import urllib.request

from config import Settings


class ChromeManager:
    """Manages Chrome browser process for CDP connection."""

    process = None

    @classmethod
    def launch(cls, port: int = 9222) -> subprocess.Popen:
        """Launch Chrome with remote debugging enabled."""
        # Kill any existing Chrome debug instances
        subprocess.run(['pkill', '-f', 'Chrome.*remote-debugging'], capture_output=True)
        time.sleep(1)

        chrome_path = Settings.CHROME_PATH

        # Create a temporary profile directory
        profile_dir = f"/tmp/chrome-debug-profile-{port}"

        cmd = [
            chrome_path,
            f"--remote-debugging-port={port}",
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-default-apps",
            "--disable-popup-blocking",
            "--disable-translate",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-device-discovery-notifications",
            "--window-size=1920,1080",
            "about:blank"
        ]

        # Launch Chrome in background
        cls.process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            preexec_fn=os.setpgrp
        )

        # Wait for Chrome to be ready (check if debugging port is open)
        for i in range(10):
            time.sleep(1)
            try:
                urllib.request.urlopen(f"http://127.0.0.1:{port}/json/version", timeout=1)
                print(f"    Chrome started on port {port}")
                break
            except Exception:
                if i == 9:
                    print("    Warning: Chrome may not have started properly")

        return cls.process

    @classmethod
    def cleanup(cls) -> None:
        """Clean up Chrome process on exit."""
        # First try to kill the tracked process
        if cls.process:
            try:
                # Try SIGTERM first (graceful)
                os.killpg(os.getpgid(cls.process.pid), signal.SIGTERM)
                time.sleep(1)
            except Exception:
                pass

            try:
                # Force kill if still running
                if cls.process.poll() is None:
                    os.killpg(os.getpgid(cls.process.pid), signal.SIGKILL)
            except Exception:
                pass

            cls.process = None

        # Also kill any remaining Chrome debug instances
        try:
            subprocess.run(
                ['pkill', '-f', 'Chrome.*remote-debugging'],
                capture_output=True,
                timeout=5
            )
        except Exception:
            pass

        print("    Chrome process cleaned up")

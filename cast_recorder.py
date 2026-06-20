"""
Record the real mouse timing used to cast the fishing rod.

Usage:
  1. Run this script as Administrator.
  2. Put the game in the exact state where you normally cast.
  3. Press F9 to arm recording.
  4. Perform the cast manually.
  5. Press F9 again to save cast_profile.json.
  6. Run fishing_macro.py; it will replay this profile automatically.
"""

import ctypes
import json
import os
import time
from datetime import datetime

import keyboard


PROFILE_FILE = "cast_profile.json"
START_STOP_KEY = "F9"
CANCEL_KEY = "ESC"
POLL_INTERVAL = 0.002

VK_LBUTTON = 0x01
VK_RBUTTON = 0x02


def is_admin():
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def mouse_pressed(vk_code):
    return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)


def wait_for_key_release(key):
    while keyboard.is_pressed(key):
        time.sleep(0.03)


def print_header():
    print()
    print("=" * 58)
    print("  RedM Fishing Macro - Cast Timing Recorder")
    print("=" * 58)
    print(f"  {START_STOP_KEY}  = start / save recording")
    print(f"  {CANCEL_KEY} = cancel without saving")
    print()


def record_events():
    print(f"Press {START_STOP_KEY} when you are ready to cast.")
    keyboard.wait(START_STOP_KEY)
    wait_for_key_release(START_STOP_KEY)

    print("Recording... perform the cast now.")
    print(f"Press {START_STOP_KEY} again to save, or {CANCEL_KEY} to cancel.")

    start = time.perf_counter()
    events = []
    previous = {
        "left": mouse_pressed(VK_LBUTTON),
        "right": mouse_pressed(VK_RBUTTON),
    }

    while True:
        if keyboard.is_pressed(CANCEL_KEY):
            wait_for_key_release(CANCEL_KEY)
            print("Cancelled. No profile was saved.")
            return None

        if keyboard.is_pressed(START_STOP_KEY):
            wait_for_key_release(START_STOP_KEY)
            break

        current = {
            "left": mouse_pressed(VK_LBUTTON),
            "right": mouse_pressed(VK_RBUTTON),
        }

        for button in ("left", "right"):
            if current[button] != previous[button]:
                action = "down" if current[button] else "up"
                at = round(time.perf_counter() - start, 4)
                events.append({
                    "type": "mouse",
                    "button": button,
                    "action": action,
                    "at": at,
                })
                print(f"  {at:>7.4f}s  {button:>5} {action}")

        previous = current
        time.sleep(POLL_INTERVAL)

    return events


def save_profile(events):
    if not events:
        print("No mouse events were recorded. Profile was not saved.")
        return False

    # Make sure no button is left logically held in replay.
    held = set()
    for event in events:
        button = event["button"]
        if event["action"] == "down":
            held.add(button)
        elif event["action"] == "up":
            held.discard(button)

    last_at = events[-1]["at"]
    for button in sorted(held):
        last_at = round(last_at + 0.02, 4)
        events.append({
            "type": "mouse",
            "button": button,
            "action": "up",
            "at": last_at,
        })

    profile = {
        "version": 1,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "description": "Recorded cast timing for fishing_macro.py",
        "events": events,
    }

    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), PROFILE_FILE)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    print()
    print(f"Saved {len(events)} events to: {path}")
    print("Run fishing_macro.py normally; it will use this cast profile automatically.")
    return True


def main():
    print_header()

    if not is_admin():
        print("Warning: this is not running as Administrator.")
        print("Mouse/key hooks may be blocked by RedM. Run as Administrator if recording is unreliable.")
        print()

    events = record_events()
    if events is not None:
        save_profile(events)


if __name__ == "__main__":
    main()

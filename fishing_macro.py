"""
=============================================================
  🎣 RedM Fishing Macro v1.0
  สำหรับ Downtown RP Server
=============================================================
  Controls:
    F9  - เริ่ม macro
    F10 - หยุด macro
    Ctrl+C - ออกจากโปรแกรม

  Usage:
    1. รันโปรแกรมนี้
    2. เปิดเกม RedM (Borderless Windowed)
    3. ยืนที่จุดตกปลา
    4. กด F9 เพื่อเริ่ม

  Template Setup:
    รันด้วย --capture เพื่อจับภาพ template จากเกม:
    python fishing_macro.py --capture
=============================================================
"""

import pyautogui
import pydirectinput
pydirectinput.FAILSAFE = False
import cv2
import numpy as np
from PIL import ImageGrab
import keyboard
import time
import os
import sys
import threading
from datetime import datetime
import ctypes
import json


def is_admin():
    """Check if the script is running with administrative privileges"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


# Mouse event constants for legacy Windows API (works in Raw Input mode)
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010

def legacy_mouse_down(button='left'):
    """Send mouse down event using legacy mouse_event API to bypass Raw Input block"""
    if button == 'left':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    elif button == 'right':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)

def legacy_mouse_up(button='left'):
    """Send mouse up event using legacy mouse_event API to bypass Raw Input block"""
    if button == 'left':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    elif button == 'right':
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)


def replay_mouse_event(button, action):
    """Replay one mouse action using the legacy Windows API."""
    if action == "down":
        legacy_mouse_down(button)
    elif action == "up":
        legacy_mouse_up(button)


# ==================== CONFIGURATION ====================
# ปรับค่าตรงนี้ได้ตามต้องการ

START_KEY = "F9"           # ปุ่มเริ่ม macro
STOP_KEY = "F10"           # ปุ่มหยุด macro

# Delays (วินาที)
DELAY_OPEN_INVENTORY = 1.5       # รอหลังเปิดกระเป๋า
DELAY_AFTER_CLICK_LURE = 0.8     # รอหลังคลิกเหยื่อ
DELAY_AFTER_USE = 0.5            # รอหลังกดใช้
DELAY_BAIT_ANIMATION = 5.0       # รอ Animation ใส่เหยื่อ
DELAY_CAST_HOLD_RIGHT = 1.5     # คลิกขวาค้าง 1 วิ
DELAY_BEFORE_LEFT_CLICK = 0.5    # ดีเลย์ก่อนกดคลิกซ้าย 0.5 วิ
DELAY_AFTER_CAST = 2.0           # รอหลังเหวี่ยงเบ็ด
DELAY_AFTER_PICKUP = 0.3         # รอหลังเก็บปลา
DELAY_BETWEEN_ROUNDS = 0.3       # พักระหว่างรอบ

CAST_PROFILE_FILE = "cast_profile.json"  # Optional recorded cast timing profile

# Detection Thresholds
TEMPLATE_CONFIDENCE = 0.7        # ค่าความมั่นใจ template matching (0.0-1.0)
USE_BUTTON_CONFIDENCE = 0.88     # ปุ่ม "ใช้" ต้องเข้มกว่าปกติ เพราะคำไทยบางคำหน้าตาใกล้กัน
MINIGAME_CONFIDENCE = 0.6        # ค่าความมั่นใจสำหรับมินิเกม
HOOK_DISTANCE_THRESHOLD = 30     # ปรับระยะพิกเซลเป็น 30 เพื่อป้องกันไอคอนวิ่งทะลุขอบเขตในเฟรมเดียว
MINIGAME_PRESS_DISTANCE = 12     # กด SPACE เมื่อ center ของ hook/target ใกล้กันไม่เกินค่านี้
MINIGAME_PREDICTION_LEAD = 0.06  # คาดการณ์ตำแหน่งล่วงหน้าเพื่อชดเชย input/screenshot latency
MINIGAME_PRESS_COOLDOWN = 0.12   # เว้นระยะกด SPACE ซ้ำ

# Mini-game Color Detection (HSV ranges)
# สีม่วง (วงกลมเป้าหมาย)
PURPLE_H_LOW, PURPLE_H_HIGH = 115, 165
PURPLE_S_LOW, PURPLE_S_HIGH = 40, 255
PURPLE_V_LOW, PURPLE_V_HIGH = 40, 255

# Timeout (วินาที)
TIMEOUT_FIND_LURE = 10           # รอหาเหยื่อนานสุด
TIMEOUT_FIND_USE = 8             # รอหาปุ่มใช้นานสุด
TIMEOUT_WAIT_BITE = 120          # รอปลากัดนานสุด
TIMEOUT_WAIT_PICKUP = 20         # รอ PICKUP นานสุด
MINIGAME_MAX_ATTEMPTS = 2000      # ลองจับจังหวะมินิเกมสูงสุด

# ==================== END CONFIG ====================

# Pyautogui settings
pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True  # เลื่อนเมาส์ไปมุมจอเพื่อหยุดฉุกเฉิน
pydirectinput.PAUSE = 0.05


class Colors:
    """ANSI Console Colors"""
    RESET = "\033[0m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def log(msg, color=Colors.WHITE):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.CYAN}[{timestamp}]{Colors.RESET} {color}{msg}{Colors.RESET}")


def log_step(step_num, msg):
    """Print step header"""
    icons = {1: "📦", 2: "🔍", 3: "👆", 4: "⏳", 5: "🎣", 6: "🎮", 7: "🐟"}
    icon = icons.get(step_num, "▶")
    log(f"{icon} Step {step_num}: {msg}", Colors.BOLD + Colors.BLUE)


class FishingMacro:
    """Main Fishing Macro Controller"""

    def __init__(self):
        self.running = False
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.templates_dir = os.path.join(self.script_dir, "templates")
        self.fish_count = 0
        self.round_count = 0
        self._thread = None

        # Ensure templates directory
        os.makedirs(self.templates_dir, exist_ok=True)

        # Load templates
        self.templates = {}
        self._load_all_templates()
        self.cast_profile = self._load_cast_profile()

    # ========== TEMPLATE LOADING ==========

    def _load_all_templates(self):
        """Load all template images from disk"""
        template_files = {
            "lure": "lure.png",
            "use_button": "use_button.png",
            "minigame": "minigame_bar.png",
            "hook": "hook_icon.png",
            "lure_icon": "lure_icon.png",
            "pickup": "pickup_prompt.png",
            "escaped": "escaped.png",
        }

        loaded = 0
        missing = []

        for name, filename in template_files.items():
            path = os.path.join(self.templates_dir, filename)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    self.templates[name] = img
                    log(f"  ✅ {filename} ({img.shape[1]}x{img.shape[0]}px)", Colors.GREEN)
                    loaded += 1
                else:
                    missing.append(filename)
                    log(f"  ❌ อ่านไฟล์ไม่ได้: {filename}", Colors.RED)
            else:
                missing.append(filename)
                log(f"  ⚠️  ไม่พบ: {filename}", Colors.YELLOW)

        log(f"\n  📂 โหลดได้ {loaded}/{len(template_files)} templates", Colors.CYAN)

        if missing:
            log(f"  ⚠️  ขาด template {len(missing)} ไฟล์:", Colors.YELLOW)
            for f in missing:
                log(f"     - {f}", Colors.YELLOW)
            log(f"\n  💡 วิธีสร้าง template:", Colors.CYAN)
            log(f"     python fishing_macro.py --capture", Colors.CYAN)
            log(f"     หรือวาง screenshot ใน: {self.templates_dir}\n", Colors.CYAN)

    # ========== SCREEN DETECTION ==========

    def _load_cast_profile(self):
        """Load recorded cast timing events if cast_profile.json exists."""
        path = os.path.join(self.script_dir, CAST_PROFILE_FILE)
        if not os.path.exists(path):
            return None

        try:
            with open(path, "r", encoding="utf-8") as f:
                profile = json.load(f)

            events = profile.get("events", [])
            if not events:
                log(f"  Warning: {CAST_PROFILE_FILE} has no events; using default cast", Colors.YELLOW)
                return None

            valid_events = []
            for event in events:
                if event.get("type") != "mouse":
                    continue
                button = event.get("button")
                action = event.get("action")
                at = event.get("at")
                if button not in ("left", "right") or action not in ("down", "up"):
                    continue
                if not isinstance(at, (int, float)) or at < 0:
                    continue
                valid_events.append({"button": button, "action": action, "at": float(at)})

            if not valid_events:
                log(f"  Warning: {CAST_PROFILE_FILE} has no usable mouse events; using default cast", Colors.YELLOW)
                return None

            valid_events.sort(key=lambda event: event["at"])
            log(f"  Loaded cast profile: {len(valid_events)} mouse events from {CAST_PROFILE_FILE}", Colors.GREEN)
            return {"events": valid_events}
        except Exception as e:
            log(f"  Warning: could not load {CAST_PROFILE_FILE}: {e}", Colors.YELLOW)
            return None

    def replay_cast_profile(self):
        """Replay the recorded cast profile. Returns True when a profile was used."""
        if not self.cast_profile:
            return False

        log_step(5, f"Replaying recorded cast profile ({CAST_PROFILE_FILE})")
        start = time.perf_counter()
        pressed = set()

        try:
            for event in self.cast_profile["events"]:
                if not self.running:
                    break

                wait_for = event["at"] - (time.perf_counter() - start)
                if wait_for > 0:
                    time.sleep(wait_for)

                replay_mouse_event(event["button"], event["action"])
                if event["action"] == "down":
                    pressed.add(event["button"])
                else:
                    pressed.discard(event["button"])

            for button in list(pressed):
                replay_mouse_event(button, "up")

            log("  Recorded cast replay complete. Waiting for bite...", Colors.GREEN)
            time.sleep(DELAY_AFTER_CAST)
            return True
        except Exception as e:
            for button in ("left", "right"):
                replay_mouse_event(button, "up")
            log(f"  Recorded cast failed ({e}); falling back to default cast", Colors.YELLOW)
            return False

    def screenshot(self, region=None):
        """
        Capture screen.
        region = (x, y, width, height) or None for full screen
        """
        if region:
            x, y, w, h = region
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        else:
            img = ImageGrab.grab()
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def find_on_screen(self, template_name, threshold=None, region=None):
        """
        Find a template image on screen.
        Returns (center_x, center_y, confidence) or None
        """
        template = self.templates.get(template_name)
        if template is None:
            return None

        if threshold is None:
            threshold = TEMPLATE_CONFIDENCE

        screen = self.screenshot(region)

        # Ensure screen is large enough
        if (screen.shape[0] < template.shape[0] or
                screen.shape[1] < template.shape[1]):
            return None

        result = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2

            # Offset by region origin
            if region:
                cx += region[0]
                cy += region[1]

            return (cx, cy, max_val)
        return None

    def wait_for_template(self, template_name, timeout, threshold=None, interval=0.5, region=None):
        """
        Wait for a template to appear on screen.
        Returns position or None if timeout.
        """
        start = time.time()
        while time.time() - start < timeout:
            if not self.running:
                return None
            pos = self.find_on_screen(template_name, threshold, region=region)
            if pos:
                return pos
            time.sleep(interval)
        return None

    def find_purple_circle_x(self, bar_region):
        """Find X position of the purple circle in mini-game bar"""
        screen = self.screenshot(bar_region)
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

        lower = np.array([PURPLE_H_LOW, PURPLE_S_LOW, PURPLE_V_LOW])
        upper = np.array([PURPLE_H_HIGH, PURPLE_S_HIGH, PURPLE_V_HIGH])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 15:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    return int(M["m10"] / M["m00"]) + bar_region[0]
        return None

    def find_hook_x(self, bar_region):
        """Find X position of the hook icon in mini-game bar"""
        # Method 1: Template matching
        pos = self.find_on_screen("hook", threshold=0.55, region=bar_region)
        if pos:
            return pos[0]

        # Method 2: Detect white/light-colored hook by color
        screen = self.screenshot(bar_region)
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

        # White/light elements
        lower = np.array([0, 0, 190])
        upper = np.array([180, 60, 255])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            valid = [c for c in contours if 8 < cv2.contourArea(c) < 3000]
            if valid:
                # Pick the one closest to vertical center (likely the hook)
                bar_h = bar_region[3]
                best = None
                best_dist = float('inf')
                for c in valid:
                    M = cv2.moments(c)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        dist = abs(cy - bar_h // 2)
                        if dist < best_dist:
                            best_dist = dist
                            best = c

                if best is not None:
                    M = cv2.moments(best)
                    if M["m00"] > 0:
                        return int(M["m10"] / M["m00"]) + bar_region[0]
        return None

    def match_template_on_image(self, image, template_name, threshold=None):
        """Find a template image on a pre-captured image. Returns (center_x, center_y, confidence) or None"""
        template = self.templates.get(template_name)
        if template is None or image is None:
            return None

        if threshold is None:
            threshold = TEMPLATE_CONFIDENCE

        # Ensure image is large enough
        if (image.shape[0] < template.shape[0] or
                image.shape[1] < template.shape[1]):
            return None

        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            cx = max_loc[0] + w // 2
            cy = max_loc[1] + h // 2
            return (cx, cy, max_val)
        return None

    def find_template_bbox_on_image(self, image, template_name, threshold=None):
        """Find a template image on a pre-captured image. Returns (x, y, w, h, confidence) or None"""
        template = self.templates.get(template_name)
        if template is None or image is None:
            return None

        if threshold is None:
            threshold = TEMPLATE_CONFIDENCE

        # Ensure image is large enough
        if (image.shape[0] < template.shape[0] or
                image.shape[1] < template.shape[1]):
            return None

        result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= threshold:
            h, w = template.shape[:2]
            return (max_loc[0], max_loc[1], w, h, max_val)
        return None

    def find_purple_circle_x_on_image(self, screen, x_offset):
        """Find X position of the purple circle in pre-captured image"""
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

        lower = np.array([PURPLE_H_LOW, PURPLE_S_LOW, PURPLE_V_LOW])
        upper = np.array([PURPLE_H_HIGH, PURPLE_S_HIGH, PURPLE_V_HIGH])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest) > 15:
                M = cv2.moments(largest)
                if M["m00"] > 0:
                    return int(M["m10"] / M["m00"]) + x_offset
        return None

    def find_hook_x_on_image(self, screen, x_offset):
        """Find X position of the hook icon in pre-captured image"""
        # Method 1: Template matching
        pos = self.match_template_on_image(screen, "hook", threshold=0.55)
        if pos:
            return pos[0] + x_offset

        # Method 2: Detect white/light-colored hook by color
        hsv = cv2.cvtColor(screen, cv2.COLOR_BGR2HSV)

        # White/light elements
        lower = np.array([0, 0, 190])
        upper = np.array([180, 60, 255])
        mask = cv2.inRange(hsv, lower, upper)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            valid = [c for c in contours if 8 < cv2.contourArea(c) < 3000]
            if valid:
                bar_h = screen.shape[0]
                best = None
                best_dist = float('inf')
                for c in valid:
                    M = cv2.moments(c)
                    if M["m00"] > 0:
                        cy = int(M["m01"] / M["m00"])
                        dist = abs(cy - bar_h // 2)
                        if dist < best_dist:
                            best_dist = dist
                            best = c

                if best is not None:
                    M = cv2.moments(best)
                    if M["m00"] > 0:
                        return int(M["m10"] / M["m00"]) + x_offset
        return None

    def is_minigame_active(self):
        """Check if mini-game is still on screen"""
        return self.find_on_screen("minigame", threshold=0.5) is not None

    # ========== MACRO STEPS ==========

    def step1_open_inventory(self):
        """Step 1: Press I to open inventory"""
        log_step(1, "กดปุ่ม I เปิดกระเป๋า")
        pydirectinput.press('i')
        time.sleep(DELAY_OPEN_INVENTORY)

    def step2_find_lure(self):
        """Step 2: Find lure in inventory and click it. Returns False if not found (bait depleted)."""
        log_step(2, "สแกนหาเหยื่อตกปลา...")

        pos = self.wait_for_template("lure", TIMEOUT_FIND_LURE, interval=0.5)
        if pos:
            log(f"  ✅ เจอเหยื่อที่ ({pos[0]}, {pos[1]}) [{pos[2]:.0%}]", Colors.GREEN)
            pyautogui.click(pos[0], pos[1])
            time.sleep(DELAY_AFTER_CLICK_LURE)
            return True

        log("  ❌ ไม่เจอเหยื่อในกระเป๋า — เหยื่อหมดแล้ว!", Colors.RED)
        return False

    def step3_click_use(self):
        """Step 3: Find and click 'ใช้' button. Returns False if not found."""
        log_step(3, "สแกนหาปุ่ม 'ใช้'...")

        screen_w, screen_h = pyautogui.size()
        action_region = (0, int(screen_h * 0.55), screen_w, int(screen_h * 0.45))
        pos = self.wait_for_template(
            "use_button",
            TIMEOUT_FIND_USE,
            threshold=USE_BUTTON_CONFIDENCE,
            interval=0.3,
            region=action_region,
        )
        if pos:
            log(f"  ✅ เจอปุ่ม 'ใช้' ที่ ({pos[0]}, {pos[1]})", Colors.GREEN)
            pyautogui.click(pos[0], pos[1])
            time.sleep(DELAY_AFTER_USE)
            return True

        log("  ❌ ไม่เจอปุ่ม 'ใช้'", Colors.RED)
        return False

    def step4_wait_animation(self):
        """Step 4: Wait for bait equip animation"""
        log_step(4, f"รอ Animation ใส่เหยื่อ ({DELAY_BAIT_ANIMATION:.0f} วินาที)")
        remaining = DELAY_BAIT_ANIMATION
        while remaining > 0 and self.running:
            secs = min(remaining, 1.0)
            time.sleep(secs)
            remaining -= secs
            if remaining > 0:
                log(f"  ⏳ เหลือ {remaining:.0f} วิ...", Colors.DIM)
        log("  ✅ เสร็จ!", Colors.GREEN)

    def step5_cast_rod(self):
        """Step 5: Right click hold -> delay -> left click -> release all"""
        if self.replay_cast_profile():
            return
        log_step(5, "เหวี่ยงเบ็ด (คลิกขวาค้าง 1 วิ -> ดีเลย์ 0.5 วิ -> คลิกซ้าย 1 ที -> ปล่อยปุ่ม)")

        # กดคลิกขวาค้างไว้เพื่อเล็งเบ็ด
        pyautogui.mouseDown(button='right')
        time.sleep(DELAY_CAST_HOLD_RIGHT)

        # ดีเลย์ 0.5 วิ ก่อนกดคลิกซ้าย
        time.sleep(DELAY_BEFORE_LEFT_CLICK)
        
        # กดคลิกซ้าย 1 ทีไม่ต้องกดค้าง (คลิกปุ๊บปล่อยปั๊บ)
        pyautogui.click(button='left')
        
        # จากนั้นปล่อยคลิกขวา (ซ้ายปล่อยไปแล้วตอนสั่ง click)
        pyautogui.mouseUp(button='right')

        log("  ✅ เหวี่ยงเบ็ดแล้ว! รอปลากัด...", Colors.GREEN)
        time.sleep(DELAY_AFTER_CAST)

    def step6_minigame(self):
        """Step 6: Detect and play the fishing mini-game. Returns False if fish escaped, True otherwise."""
        log_step(6, "รอมินิเกมตกปลา...")

        # --- Wait for mini-game to appear ---
        start_time = time.time()
        pos = None
        screen_w, screen_h = pyautogui.size()
        escaped_region = (screen_w // 2, 0, screen_w // 2, screen_h) # หาข้อความปลาหนีเฉพาะครึ่งขวาของจอ

        while time.time() - start_time < TIMEOUT_WAIT_BITE:
            if not self.running:
                return False
            
            pos = self.find_on_screen("minigame", threshold=MINIGAME_CONFIDENCE)
            if pos:
                break
                
            if "escaped" in self.templates:
                pos_escaped = self.find_on_screen("escaped", threshold=0.8, region=escaped_region)
                if pos_escaped:
                    log("  ❌ ตรวจพบข้อความ 'ปลาหนี' ก่อนเริ่มมินิเกม! เริ่มรอบใหม่", Colors.RED)
                    return False

            time.sleep(0.5)

        if not pos:
            log("  ⚠️ ไม่เจอมินิเกม (หมดเวลารอ)", Colors.YELLOW)
            return True

        log("  🎮 มินิเกมปรากฏ! เริ่มจับจังหวะ...", Colors.PURPLE)

        # --- Estimate the bar region from the detected position ---
        screen_w, screen_h = pyautogui.size()
        # The bar is typically centered horizontally, near the detected SPACE text
        bar_w = int(screen_w * 0.35)
        bar_h = int(screen_h * 0.08)
        bar_x = pos[0] - bar_w // 2
        bar_y = pos[1] - int(bar_h * 0.3)

        # Clamp to screen bounds
        bar_x = max(0, bar_x)
        bar_y = max(0, bar_y)
        bar_w = min(bar_w, screen_w - bar_x)
        bar_h = min(bar_h, screen_h - bar_y)

        bar_region = (bar_x, bar_y, bar_w, bar_h)
        log(f"  📐 บริเวณแถบ: ({bar_x},{bar_y}) {bar_w}x{bar_h}px", Colors.DIM)

        # --- Play the mini-game ---
        space_presses = 0
        check_interval = 50  # Check if still active every 50 iterations (~0.75s)
        inactive_count = 0
        last_hook_x = None
        last_sample_time = None
        hook_velocity = 0.0
        last_space_time = 0.0

        for attempt in range(MINIGAME_MAX_ATTEMPTS):
            if not self.running:
                return False

            # Periodically check if mini-game ended or fish escaped
            if attempt > 0 and attempt % check_interval == 0:
                # 1. เช็คว่ามีข้อความปลาหนีไหม
                if "escaped" in self.templates:
                    pos_escaped = self.find_on_screen("escaped", threshold=0.8, region=escaped_region)
                    if pos_escaped:
                        log("  ❌ ตรวจพบข้อความ 'ปลาหนี' ระหว่างมินิเกม! เริ่มรอบใหม่", Colors.RED)
                        return False

                # 2. เช็คว่าแถบมินิเกมยังอยู่ไหม
                if not self.is_minigame_active():
                    inactive_count += 1
                    if inactive_count >= 3:
                        log("  🎮 มินิเกมจบลงแล้ว (ไม่พบแถบมินิเกม 3 ครั้งติดต่อกัน)", Colors.PURPLE)
                        return True
                else:
                    inactive_count = 0

            # Capture screen region ONCE to achieve very high scanning FPS
            screen = self.screenshot(bar_region)

            # Find bounding boxes on the pre-captured screen
            hook_bbox = self.find_template_bbox_on_image(screen, "hook", threshold=0.4)
            lure_icon_bbox = self.find_template_bbox_on_image(screen, "lure_icon", threshold=0.4)

            if hook_bbox is not None and lure_icon_bbox is not None:
                hx, hy, hw, hh, h_conf = hook_bbox
                lx, ly, lw, lh, l_conf = lure_icon_bbox
                hook_x = hx + (hw / 2)
                target_x = lx + (lw / 2)
                now = time.perf_counter()

                if last_hook_x is not None and last_sample_time is not None:
                    dt = now - last_sample_time
                    if dt > 0:
                        instant_velocity = (hook_x - last_hook_x) / dt
                        hook_velocity = (hook_velocity * 0.55) + (instant_velocity * 0.45)

                last_hook_x = hook_x
                last_sample_time = now

                predicted_hook_x = hook_x + (hook_velocity * MINIGAME_PREDICTION_LEAD)
                distance = abs(predicted_hook_x - target_x)
                ready_for_next_press = (now - last_space_time) >= MINIGAME_PRESS_COOLDOWN

                if distance <= MINIGAME_PRESS_DISTANCE and ready_for_next_press:
                    pydirectinput.keyDown('space')
                    time.sleep(0.025)
                    pydirectinput.keyUp('space')
                    last_space_time = time.perf_counter()
                    space_presses += 1
                    log(
                        f"  SPACE! (distance: {distance:.1f}px, velocity: {hook_velocity:.0f}px/s) [#{space_presses}]",
                        Colors.GREEN
                    )
                    continue

                # คำนวณพื้นที่ทับซ้อน (Intersection)
                x_left = max(hx, lx)
                y_top = max(hy, ly)
                x_right = min(hx + hw, lx + lw)
                y_bottom = min(hy + hh, ly + lh)

                if x_right > x_left and y_bottom > y_top:
                    intersection_area = (x_right - x_left) * (y_bottom - y_top)
                    
                    # ใช้ขนาดของไอคอนที่เล็กกว่าเป็นฐานคิดเปอร์เซ็นต์ เพื่อป้องกันปัญหาการครอปภาพมาใหญ่เกินไป
                    min_area = min(hw * hh, lw * lh)
                    overlap_percent = (intersection_area / min_area) * 100

                    if False and overlap_percent >= 55.0:
                        pydirectinput.keyDown('space')
                        time.sleep(0.03)  # กดค้างนิดนึงให้เกมรับรู้
                        pydirectinput.keyUp('space')
                        space_presses += 1
                        log(f"  ⚡ SPACE! (ทับซ้อน: {overlap_percent:.1f}%) [#{space_presses}]", Colors.GREEN)
                        time.sleep(0.05)  # ลดเวลาดีเลย์ลงจาก 0.25 เพื่อให้กดย้ำได้เร็วขึ้น
                        continue

            # Sleep briefly (5ms) to run fast without pinning CPU
            time.sleep(0.005)

        log(f"  ✅ มินิเกมจบ! กด SPACE ไป {space_presses} ครั้ง", Colors.GREEN)
        time.sleep(1)
        return True

    def step7_pickup_fish(self):
        """Step 7: Wait for PICKUP prompt or fish escaped prompt. Returns False if fish escaped or timeout."""
        log_step(7, "รอข้อความ PICKUP หรือ ปลาหนี...")

        start_time = time.time()
        while time.time() - start_time < TIMEOUT_WAIT_PICKUP:
            if not self.running:
                return False

            # Check for pickup prompt (G)
            pos_pickup = self.find_on_screen("pickup", threshold=MINIGAME_CONFIDENCE)
            if pos_pickup:
                self.fish_count += 1
                log(f"  ✅ เจอ PICKUP! กด G เก็บปลา 🐟", Colors.GREEN)
                pydirectinput.press('g')
                time.sleep(DELAY_AFTER_PICKUP)
                log(f"  🐟 เก็บปลาสำเร็จ! (รวม: {self.fish_count} ตัว)", Colors.BOLD + Colors.GREEN)
                return True

            # Check for fish escaped warning (escaped.png) if template exists
            if "escaped" in self.templates:
                pos_escaped = self.find_on_screen("escaped", threshold=0.8)
                if pos_escaped:
                    log("  ❌ ตรวจพบข้อความ 'ปลาหนี'! ยกเลิกการรอและใส่เบ็ดใหม่ทันที 🎣", Colors.RED)
                    return False

            time.sleep(0.4)

        log("  ⚠️ ไม่เจอ PICKUP (หมดเวลารอ)", Colors.YELLOW)
        return False

    # ========== MAIN LOOP ==========

    def start(self):
        """Start the macro (called by F9)"""
        if self.running:
            log("⚠️ Macro กำลังทำงานอยู่แล้ว!", Colors.YELLOW)
            return

        self.running = True
        self.round_count = 0
        self.fish_count = 0

        log("", Colors.GREEN)
        log("🎣 ╔══════════════════════════════════╗", Colors.BOLD + Colors.GREEN)
        log("🎣 ║   FISHING MACRO เริ่มทำงาน!      ║", Colors.BOLD + Colors.GREEN)
        log("🎣 ╚══════════════════════════════════╝", Colors.BOLD + Colors.GREEN)
        log(f"   กด {STOP_KEY} เพื่อหยุด", Colors.YELLOW)
        log("", Colors.GREEN)

        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the macro (called by F10)"""
        if not self.running:
            return

        self.running = False

        log("", Colors.RED)
        log("🛑 ╔══════════════════════════════════╗", Colors.BOLD + Colors.RED)
        log("🛑 ║   FISHING MACRO หยุดทำงาน        ║", Colors.BOLD + Colors.RED)
        log("🛑 ╚══════════════════════════════════╝", Colors.BOLD + Colors.RED)
        log(f"   📊 ผลรวม: {self.fish_count} ตัว จาก {self.round_count} รอบ", Colors.CYAN)
        log(f"   กด {START_KEY} เพื่อเริ่มใหม่\n", Colors.YELLOW)

    def _run_loop(self):
        """Main macro loop — runs in separate thread"""
        try:
            while self.running:
                self.round_count += 1

                log(f"\n{'═' * 45}", Colors.CYAN)
                log(f"🔄 รอบที่ {self.round_count}  |  ปลาที่ได้: {self.fish_count} ตัว", Colors.BOLD + Colors.CYAN)
                log(f"{'═' * 45}", Colors.CYAN)

                # Step 1: Open inventory
                self.step1_open_inventory()
                if not self.running:
                    break

                # Step 2: Find and click lure
                if not self.step2_find_lure():
                    log("\n🛑 เหยื่อหมดแล้ว! หยุด macro อัตโนมัติ", Colors.BOLD + Colors.RED)
                    log(f"   📊 ผลรวม: {self.fish_count} ตัว จาก {self.round_count} รอบ\n", Colors.CYAN)
                    self.running = False
                    break
                if not self.running:
                    break

                # Step 3: Click 'ใช้' button
                if not self.step3_click_use():
                    log("  ⚠️ ข้ามรอบนี้ (กด ESC ปิดเมนู)", Colors.YELLOW)
                    pydirectinput.press('escape')
                    time.sleep(1)
                    continue
                if not self.running:
                    break

                # Step 4: Wait for bait animation
                self.step4_wait_animation()
                if not self.running:
                    break

                # Step 5: Cast rod
                self.step5_cast_rod()
                if not self.running:
                    break

                # Step 6: Mini-game
                if self.step6_minigame() is False:
                    # ถ้าปลาหนี (Return False) ให้เริ่มรอบใหม่ทันที
                    log(f"✅ เริ่มรอบใหม่...", Colors.GREEN)
                    time.sleep(DELAY_BETWEEN_ROUNDS)
                    continue
                    
                if not self.running:
                    break

                # Step 7: Pickup fish
                self.step7_pickup_fish()
                if not self.running:
                    break

                # Brief pause between rounds
                log(f"✅ จบรอบที่ {self.round_count}! พัก {DELAY_BETWEEN_ROUNDS:.0f} วิ...", Colors.GREEN)
                time.sleep(DELAY_BETWEEN_ROUNDS)

        except pyautogui.FailSafeException:
            log("\n🛑 FAILSAFE! เลื่อนเมาส์ไปมุมจอ — หยุด macro", Colors.BOLD + Colors.RED)
            self.running = False
        except Exception as e:
            log(f"\n❌ เกิดข้อผิดพลาด: {e}", Colors.RED)
            self.running = False


# ==================== TEMPLATE CAPTURE MODE ====================

def capture_templates():
    """Interactive template capture — ให้ผู้ใช้จับภาพ template จากเกม"""
    os.system("")  # Enable ANSI colors

    templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
    os.makedirs(templates_dir, exist_ok=True)

    print(f"\n{'═' * 55}")
    print(f"  📸 RedM Fishing Macro — โหมดจับภาพ Template")
    print(f"{'═' * 55}\n")

    templates_to_capture = [
        ("lure.png",         "เหยื่อตกปลาในกระเป๋า (ไอคอนเหยื่อ + ตัวเลข)"),
        ("use_button.png",   "ปุ่ม 'ใช้' ในแถบ action ด้านล่าง (เฉพาะปุ่มใช้)"),
        ("minigame_bar.png", "ข้อความ [ SPACE ] ที่ปรากฏตอนมินิเกม"),
        ("hook_icon.png",    "ไอคอนเบ็ดเล็กๆ ในแถบมินิเกม"),
        ("pickup_prompt.png","ข้อความ [ G ] PICKUP ที่ปรากฏหลังตกปลาสำเร็จ"),
        ("escaped.png",      "ข้อความสีแดง/แจ้งเตือนคำว่า 'ปลาหนี' (เพื่อข้ามรอบได้เร็ว)"),
    ]

    print("  📋 วิธีใช้:")
    print("  ─────────────────────────────────────")
    print("  1. เปิดเกม RedM ไว้ข้างๆ")
    print("  2. ทำให้ UI element ที่ต้องการปรากฏบนจอ")
    print("  3. กด Enter เพื่อ screenshot ทั้งจอ")
    print("  4. หน้าต่าง OpenCV จะเปิด — ลากเมาส์เลือกพื้นที่")
    print("  5. กด SPACE หรือ ENTER เพื่อยืนยัน / กด C เพื่อยกเลิก")
    print()

    for filename, description in templates_to_capture:
        filepath = os.path.join(templates_dir, filename)

        # Check if already exists
        if os.path.exists(filepath):
            ans = input(f"  📸 {filename} มีอยู่แล้ว — ถ่ายใหม่? (y/N): ").strip().lower()
            if ans != 'y':
                print(f"     ↳ ข้าม {filename}\n")
                continue

        print(f"\n  📸 กำลังจะจับภาพ: {description}")
        print(f"     ไฟล์ปลายทาง: {filename}")
        input("     ▶ กด Enter เมื่อพร้อม (ให้ UI element แสดงบนจอ)...")

        # Slight delay for user to switch to game
        print("     ⏳ จับภาพใน 2 วินาที...")
        time.sleep(2)

        # Capture full screen
        screen = ImageGrab.grab()
        screen_np = cv2.cvtColor(np.array(screen), cv2.COLOR_RGB2BGR)

        # Let user select ROI
        print("     🖱️  ลากเมาส์เลือกพื้นที่ → กด SPACE/ENTER ยืนยัน → C ยกเลิก")
        window_name = f"Select: {description}"
        
        # Resize for display if screen is very large
        display_scale = 1.0
        disp_h, disp_w = screen_np.shape[:2]
        if disp_w > 1920:
            display_scale = 1920 / disp_w
            disp_w = 1920
            disp_h = int(screen_np.shape[0] * display_scale)
            display_img = cv2.resize(screen_np, (disp_w, disp_h))
        else:
            display_img = screen_np

        roi = cv2.selectROI(window_name, display_img, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()

        if roi[2] > 0 and roi[3] > 0:
            # Scale ROI back if we resized
            if display_scale != 1.0:
                roi = tuple(int(v / display_scale) for v in roi)

            x, y, w, h = roi
            template = screen_np[y:y + h, x:x + w]
            cv2.imwrite(filepath, template)
            print(f"     ✅ บันทึก {filename} สำเร็จ! ({w}x{h} pixels)\n")
        else:
            print(f"     ❌ ยกเลิก — ข้ามไป\n")

    print(f"\n{'═' * 55}")
    print(f"  ✅ เสร็จสิ้น!")
    print(f"  📂 Templates อยู่ใน: {templates_dir}")
    print(f"\n  ▶ รัน macro ได้เลย: python fishing_macro.py")
    print(f"{'═' * 55}\n")


# ==================== MAIN ====================

def main():
    # Enable ANSI escape codes on Windows
    os.system("")

    # Check for administrator privileges
    if not is_admin():
        print(f"\n{Colors.BOLD}{Colors.RED}============================================================={Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}  ⚠️  คำเตือน: โปรแกรมไม่ได้รันด้วยสิทธิ์ Administrator!{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.RED}============================================================={Colors.RESET}")
        print(f"  เกม RedM / GTA V มักจะบล็อกการกดปุ่มจากโปรแกรมธรรมดา")
        print(f"  กรุณาปิดหน้าต่างนี้ แล้วทำตามวิธีใดวิธีหนึ่ง:")
        print(f"    1. คลิกขวาที่ {Colors.YELLOW}run_macro.bat{Colors.RESET} แล้วเลือก {Colors.GREEN}'Run as administrator'{Colors.RESET}")
        print(f"    2. รัน Command Prompt/PowerShell ในฐานะ Administrator แล้วค่อยรันสคริปต์")
        print(f"{Colors.BOLD}{Colors.RED}─────────────────────────────────────────────────────────────{Colors.RESET}\n")

    # Capture mode
    if "--capture" in sys.argv:
        capture_templates()
        return

    # Banner
    print(f"""
{Colors.CYAN}{'═' * 50}
  🎣 RedM Fishing Macro v1.0
  🎣 Downtown RP Server — Auto Fishing Bot
{'═' * 50}{Colors.RESET}
{Colors.YELLOW}  ┌─────────────────────────────────┐
  │  {START_KEY:>3}  = เริ่ม macro               │
  │  {STOP_KEY:>3} = หยุด macro               │
  │  Ctrl+C = ออกจากโปรแกรม        │
  │  เลื่อนเมาส์ไปมุมจอ = ฉุกเฉิน  │
  └─────────────────────────────────┘{Colors.RESET}
""")

    # Load templates
    log("📂 กำลังโหลด template images...", Colors.CYAN)
    macro = FishingMacro()

    # Check if any templates are loaded
    if not macro.templates:
        log("\n❌ ไม่มี template ใดๆ! ไม่สามารถเริ่ม macro ได้", Colors.RED)
        log("   กรุณารัน: python fishing_macro.py --capture\n", Colors.YELLOW)

    # Register hotkeys
    keyboard.on_press_key(START_KEY, lambda _: macro.start(), suppress=False)
    keyboard.on_press_key(STOP_KEY, lambda _: macro.stop(), suppress=False)

    log(f"\n✅ พร้อมทำงาน! กด {START_KEY} เพื่อเริ่ม macro", Colors.BOLD + Colors.GREEN)
    log("   💡 เปิดเกม RedM แล้วยืนที่จุดตกปลา", Colors.YELLOW)
    log("   💡 เกมต้องเป็น Borderless Windowed mode\n", Colors.YELLOW)

    # Keep alive
    try:
        keyboard.wait()
    except KeyboardInterrupt:
        macro.stop()
        print(f"\n{Colors.CYAN}👋 ออกจากโปรแกรม{Colors.RESET}")
        sys.exit(0)


if __name__ == "__main__":
    main()

# Terraria Timekeeper - simple Windows reminder/monitor
# Author: ChatGPT
# Requirements: Python 3.9+, Windows 10/11
# pip install -r requirements.txt
#
# Features:
# - Choose play "duration" (h/m) or "until" a clock time (HH:MM 24h)
# - Monitors Terraria.exe in the background
# - Toast pop-ups at 5, 3, 1 minutes before planned end
# - If you quit earlier than planned, logs "early minutes" and awards points
# - Logs saved to: rewards_log.csv ; total points in rewards_total.json
#
# Notes:
# - If you start the timer with less than 5 minutes remaining, only the upcoming reminders will fire.
# - If Terraria isn't running, the app still counts down; "early" credit triggers only when the game closes before end time.
# - Close the window to stop the monitor.

import threading
import time
import csv
import os
import json
import datetime as dt
import re
import PySimpleGUI as sg
import psutil
from typing import Union, Optional

try:
    from win10toast import ToastNotifier
    _toaster = ToastNotifier()
    def show_toast(title, msg, duration=5):
        # duration is best-effort seconds
        try:
            _toaster.show_toast(title, msg, duration=duration, threaded=True, icon_path=None)
        except Exception as e:
            print(f"[toast fallback] {title}: {msg} ({e})")
except Exception as e:
    print(f"[WARNING] win10toast import failed: {e}")
    _toaster = None
    def show_toast(title, msg, duration=5):
        # Fallback: print to console if win10toast not available
        print(f"[TOAST FALLBACK] {title}: {msg}")

def show_popup_alert(message, title="Terraria Timekeeper Alert", duration=10):
    """Show a popup alert with OK button that user can close manually"""
    try:
        import PySimpleGUI as sg
        sg.popup(message, 
                title=title, 
                keep_on_top=True, 
                auto_close=True, 
                auto_close_duration=duration,
                button_type=sg.POPUP_BUTTONS_OK,
                non_blocking=False)
        return True
    except Exception as e:
        print(f"Popup alert failed: {e}")
        return False

APP_NAME = "Terraria Timekeeper"
PROCESS_NAME = "Terraria.exe"
LOG_CSV = "rewards_log.csv"
TOTAL_JSON = "rewards_total.json"
POINTS_PER_MIN_EARLY = 10  # tweak if you like

def is_process_running(name: str) -> bool:
    for p in psutil.process_iter(["name"]):
        try:
            if p.info["name"] and p.info["name"].lower() == name.lower():
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    return False

def now():
    return dt.datetime.now()

def parse_time_hhmm(s: str) -> Optional[dt.time]:
    m = re.fullmatch(r"\s*(\d{1,2}):(\d{2})\s*", s or "")
    if not m:
        return None
    hh, mm = int(m.group(1)), int(m.group(2))
    if 0 <= hh <= 23 and 0 <= mm <= 59:
        return dt.time(hh, mm)
    return None

def ensure_files():
    if not os.path.exists(LOG_CSV):
        with open(LOG_CSV, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["session_start", "mode", "planned_end", "actual_end", "early_minutes", "points_awarded"])
    if not os.path.exists(TOTAL_JSON):
        with open(TOTAL_JSON, "w", encoding="utf-8") as f:
            json.dump({"total_points": 0}, f)

def add_reward(early_minutes: int) -> int:
    points = max(0, early_minutes) * POINTS_PER_MIN_EARLY
    ensure_files()
    # write row
    with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        pass  # caller writes full row
    # update total
    try:
        data = json.load(open(TOTAL_JSON, "r", encoding="utf-8"))
    except Exception:
        data = {"total_points": 0}
    data["total_points"] = int(data.get("total_points", 0)) + points
    with open(TOTAL_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return points

class MonitorThread(threading.Thread):
    def __init__(self, planned_end: dt.datetime, mode_desc: str, session_start: dt.datetime, update_cb):
        super().__init__(daemon=True)
        self.planned_end = planned_end
        self.mode_desc = mode_desc
        self.session_start = session_start
        self.update_cb = update_cb
        self._stop = threading.Event()
        self._notified = set()  # which minute markers fired (5,3,1)
        self._done = False

    def stop(self):
        self._stop.set()

    def run(self):
        show_toast(APP_NAME, f"Timer started: {self.mode_desc}")
        terraria_was_running = False  # Track if Terraria was running at any point
        
        while not self._stop.is_set():
            now_ts = now()
            remaining = (self.planned_end - now_ts).total_seconds()
            # UI update
            self.update_cb(max(0, int(remaining)))

            if remaining <= 0:
                # Time up
                show_toast(APP_NAME, "Time's up! Prepare to wrap up.")
                # Show popup alert for time's up
                show_popup_alert("⏰ TIME'S UP!\n\nYour planned gaming time has ended.\n\nPlease save and close Terraria now!\n\nClick OK to close this reminder.", 
                               "Terraria Timekeeper - Time Up!", 15)
                self._done = True
                break

            # Pre-end reminders at 5, 3, 1 minutes if not already shown
            for m in (5, 3, 1):
                marker = m*60
                # Only trigger if we're within the specific minute range and haven't shown this notification yet
                if remaining <= marker and m not in self._notified:
                    # For 1-minute notification, only show if we're at 1 minute or less
                    if m == 1 and remaining <= 60:
                        self._notified.add(m)
                        # Show both toast notification and popup alert
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        # Create popup alert window with OK button
                        show_popup_alert(f"⏰ Terraria Reminder\n\n{m} minutes remaining!\n\nPrepare to save and close game.\n\nClick OK to close this reminder.", 
                                       "Terraria Timekeeper Alert", 10)
                    # For 3-minute notification, only show if we're between 3 and 2 minutes
                    elif m == 3 and remaining <= 180 and remaining > 120:
                        self._notified.add(m)
                        # Show both toast notification and popup alert
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        # Create popup alert window with OK button
                        show_popup_alert(f"⏰ Terraria Reminder\n\n{m} minutes remaining!\n\nPrepare to save and close game.\n\nClick OK to close this reminder.", 
                                       "Terraria Timekeeper Alert", 10)
                    # For 5-minute notification, only show if we're between 5 and 4 minutes
                    elif m == 5 and remaining <= 300 and remaining > 240:
                        self._notified.add(m)
                        # Show both toast notification and popup alert
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        # Create popup alert window with OK button
                        show_popup_alert(f"⏰ Terraria Reminder\n\n{m} minutes remaining!\n\nPrepare to save and close game.\n\nClick OK to close this reminder.", 
                                       "Terraria Timekeeper Alert", 10)

            # Check if Terraria is currently running
            terraria_running = is_process_running(PROCESS_NAME)
            if terraria_running:
                terraria_was_running = True

            # Detect early finish: Terraria closes while still remaining time
            if remaining > 0 and not terraria_running and terraria_was_running:
                minutes_early = int((self.planned_end - now_ts).total_seconds() // 60)
                if minutes_early > 0:
                    points = minutes_early * POINTS_PER_MIN_EARLY
                    # Log
                    ensure_files()
                    with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
                        w = csv.writer(f)
                        w.writerow([
                            self.session_start.strftime("%Y-%m-%d %H:%M:%S"),
                            self.mode_desc,
                            self.planned_end.strftime("%Y-%m-%d %H:%M:%S"),
                            now_ts.strftime("%Y-%m-%d %H:%M:%S"),
                            minutes_early,
                            points
                        ])
                    # Update total
                    try:
                        data = json.load(open(TOTAL_JSON, "r", encoding="utf-8"))
                    except Exception:
                        data = {"total_points": 0}
                    data["total_points"] = int(data.get("total_points", 0)) + points
                    with open(TOTAL_JSON, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                    show_toast("Early Finish Reward", f"Finished {minutes_early} minutes early! +{points} points")
                    # Show popup alert for early finish reward
                    show_popup_alert(f"🎉 Early Finish Reward!\n\nYou finished {minutes_early} minutes early!\n\n+{points} points earned!\n\nClick OK to close this reminder.", 
                                   "Terraria Timekeeper - Early Finish!", 10)
                    self._done = True
                    break

            time.sleep(1)

        self.update_cb(0)  # reset UI when done

def main():
    try:
        sg.theme("DarkBlue3")
    except Exception as e:
        print(f"Warning: Could not set theme: {e}")
        # Continue without theme
    
    layout = [
        [sg.Text("Terraria Timekeeper", font=("Segoe UI", 16, "bold"))],
        [sg.Frame("模式選擇", [
            [sg.Radio("玩幾小時/分鐘/秒", "MODE", key="-MODE_DUR-", default=True),
             sg.Text("小時"), sg.Input("0", size=(4,1), key="-H-"),
             sg.Text("分鐘"), sg.Input("30", size=(4,1), key="-M-"),
             sg.Text("秒"), sg.Input("0", size=(4,1), key="-S-")],
            [sg.Radio("玩到幾點（24小時制 HH:MM）", "MODE", key="-MODE_UNTIL-"),
             sg.Input("22:30", size=(8,1), key="-UNTIL-")]
        ])],
        [sg.Text("Terraria 狀態："), sg.Text("偵測中...", key="-STATUS-")],
        [sg.Text("剩餘時間："), sg.Text("-", key="-REMAIN-")],
        [sg.Button("開始"), sg.Button("停止"), sg.Button("退出")]
    ]

    try:
        window = sg.Window(APP_NAME, layout, finalize=True)
    except Exception as e:
        print(f"Error creating window: {e}")
        return
    monitor: Optional[MonitorThread] = None
    last_status = None

    def fmt_seconds(sec: int) -> str:
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def update_remaining(sec: int):
        try:
            window["-REMAIN-"].update(fmt_seconds(sec))
        except Exception:
            pass

    # Periodic timer
    status_timer = time.time()

    try:
        while True:
            try:
                event, values = window.read(timeout=200)
            except Exception as e:
                print(f"Window read error: {e}")
                break
                
            if event in (sg.WINDOW_CLOSED, "退出"):
                if monitor:
                    monitor.stop()
                break

            # Update Terraria running status every second-ish
            if time.time() - status_timer > 1.0:
                running = is_process_running(PROCESS_NAME)
                if running != last_status:
                    try:
                        window["-STATUS-"].update("運行中 ✅" if running else "未偵測到 ❌")
                    except Exception as e:
                        print(f"Status update error: {e}")
                    last_status = running
                status_timer = time.time()

            if event == "開始":
                if monitor and monitor.is_alive():
                    sg.popup("已在計時中。先停止再重新設定。")
                    continue

                # Compute planned_end
                session_start = now()
                if values["-MODE_DUR-"]:
                    try:
                        h = int(values["-H-"] or "0")
                        m = int(values["-M-"] or "0")
                        s = int(values["-S-"] or "0")
                        total = h*3600 + m*60 + s
                    except ValueError:
                        sg.popup_error("請輸入正確的整數（小時/分鐘/秒）。")
                        continue
                    if total <= 0:
                        sg.popup_error("時長需大於 0。")
                        continue
                    planned_end = session_start + dt.timedelta(seconds=total)
                    mode_desc = f"時長 {h}小時{m}分鐘{s}秒"
                else:
                    t = parse_time_hhmm(values["-UNTIL-"])
                    if not t:
                        sg.popup_error("請輸入 HH:MM（24小時制），例如 22:30")
                        continue
                    planned_end = dt.datetime.combine(session_start.date(), t)
                    # If that time already passed today, assume tomorrow
                    if planned_end <= session_start:
                        planned_end += dt.timedelta(days=1)
                    mode_desc = f"直到 {planned_end.strftime('%H:%M')}"

                # Start monitor thread
                monitor = MonitorThread(planned_end, mode_desc, session_start, update_cb=update_remaining)
                monitor.start()
                update_remaining(int((planned_end - now()).total_seconds()))

            if event == "停止":
                if monitor and monitor.is_alive():
                    monitor.stop()
                    monitor = None
                    update_remaining(0)
                    sg.popup("已停止。")
                else:
                    sg.popup("沒有進行中的計時。")

    except Exception as e:
        print(f"Main loop error: {e}")
    finally:
        try:
            window.close()
        except Exception as e:
            print(f"Window close error: {e}")

if __name__ == "__main__":
    print("Terraria Timekeeper starting...")
    print("Features implemented:")
    print("[OK] Duration mode (hours/minutes/seconds)")
    print("[OK] Until mode (HH:MM 24h format)")
    print("[OK] 5/3/1 minute notifications (toast + popup alerts)")
    print("[OK] Early quit detection and point system")
    print("[OK] CSV logging (rewards_log.csv)")
    print("[OK] JSON total tracking (rewards_total.json)")
    print("[OK] Terraria.exe process monitoring")
    print("-" * 50)
    try:
        main()
    except Exception as e:
        print(f"Application error: {e}")
        input("Press Enter to exit...")

#!/usr/bin/env python3
# Terraria Timekeeper - Kivy GUI Version
# Author: Cursor AI Assistant
# Requirements: Python 3.9+, Windows 10/11, Kivy
# Features:
# - Choose play "duration" (h/m/s) or "until" a clock time (HH:MM 24h)
# - Monitors Terraria.exe in the background
# - Toast pop-ups at 5, 3, 1 minutes before planned end
# - If you quit earlier than planned, logs "early minutes" and awards points
# - Logs saved to: rewards_log.csv ; total points in rewards_total.json

import threading
import time
import csv
import os
import json
import datetime as dt
import re
import psutil
from typing import Union, Optional
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.logger import Logger

try:
    from win10toast import ToastNotifier
    _toaster = ToastNotifier()
    def show_toast(title, msg, duration=5):
        # duration is best-effort seconds
        try:
            _toaster.show_toast(title, msg, duration=duration, threaded=True, icon_path=None)
        except Exception as e:
            Logger.error(f"[toast fallback] {title}: {msg} ({e})")
except Exception as e:
    Logger.warning(f"[WARNING] win10toast import failed: {e}")
    _toaster = None
    def show_toast(title, msg, duration=5):
        # Fallback: print to console if win10toast not available
        Logger.info(f"[TOAST FALLBACK] {title}: {msg}")

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

class MonitorThread(threading.Thread):
    def __init__(self, planned_end: dt.datetime, mode_desc: str, session_start: dt.datetime, app_instance):
        super().__init__(daemon=True)
        self.planned_end = planned_end
        self.mode_desc = mode_desc
        self.session_start = session_start
        self.app = app_instance
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
            
            # Update UI on main thread
            Clock.schedule_once(lambda dt: self.update_ui(remaining), 0)

            if remaining <= 0:
                # Time up
                show_toast(APP_NAME, "Time's up! Prepare to wrap up.")
                Clock.schedule_once(lambda dt: self.show_time_up_popup(), 0)
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
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        Clock.schedule_once(lambda dt, minute=m: self.show_reminder_popup(minute), 0)
                    # For 3-minute notification, only show if we're between 3 and 2 minutes
                    elif m == 3 and remaining <= 180 and remaining > 120:
                        self._notified.add(m)
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        Clock.schedule_once(lambda dt, minute=m: self.show_reminder_popup(minute), 0)
                    # For 5-minute notification, only show if we're between 5 and 4 minutes
                    elif m == 5 and remaining <= 300 and remaining > 240:
                        self._notified.add(m)
                        show_toast("Terraria Reminder", f"{m} minutes remaining - prepare to save and close game")
                        Clock.schedule_once(lambda dt, minute=m: self.show_reminder_popup(minute), 0)

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
                    Clock.schedule_once(lambda dt, early=minutes_early, pts=points: self.show_early_finish_popup(early, pts), 0)
                    self._done = True
                    break

            time.sleep(1)

        Clock.schedule_once(lambda dt: self.update_ui(0), 0)  # reset UI when done

    def update_ui(self, remaining_seconds):
        """Update UI elements on main thread"""
        if hasattr(self.app, 'root') and hasattr(self.app.root, 'ids'):
            if remaining_seconds > 0:
                m, s = divmod(int(remaining_seconds), 60)
                h, m = divmod(m, 60)
                if h > 0:
                    time_str = f"{h:02d}:{m:02d}:{s:02d}"
                else:
                    time_str = f"{m:02d}:{s:02d}"
                self.app.root.ids.remaining_label.text = time_str
                
                # Update progress bar
                total_seconds = (self.planned_end - self.session_start).total_seconds()
                progress = max(0, min(1, remaining_seconds / total_seconds))
                self.app.root.ids.progress_bar.value = progress
            else:
                self.app.root.ids.remaining_label.text = "Time's up!"
                self.app.root.ids.progress_bar.value = 0

    def show_reminder_popup(self, minutes):
        """Show reminder popup"""
        popup = Popup(
            title='Terraria Reminder',
            content=Label(text=f'{minutes} minutes remaining!\n\nPrepare to save and close game.\n\nClick OK to close this reminder.'),
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        popup.open()

    def show_time_up_popup(self):
        """Show time up popup"""
        popup = Popup(
            title='Time Up!',
            content=Label(text="Your planned gaming time has ended.\n\nPlease save and close Terraria now!\n\nClick OK to close this reminder."),
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        popup.open()

    def show_early_finish_popup(self, minutes_early, points):
        """Show early finish reward popup"""
        popup = Popup(
            title='Early Finish Reward!',
            content=Label(text=f'You finished {minutes_early} minutes early!\n\n+{points} points earned!\n\nClick OK to close this reminder.'),
            size_hint=(0.8, 0.6),
            auto_dismiss=False
        )
        popup.open()

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.monitor_thread = None
        self.build_ui()
    
    def build_ui(self):
        """Build the user interface"""
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Title
        title_label = Label(
            text='Terraria Timekeeper',
            size_hint_y=None,
            height=50,
            font_size=24,
            bold=True
        )
        main_layout.add_widget(title_label)
        
        # Mode selection
        mode_frame = BoxLayout(orientation='vertical', size_hint_y=None, height=200)
        mode_label = Label(text='Mode Selection:', size_hint_y=None, height=30, font_size=16)
        mode_frame.add_widget(mode_label)
        
        # Duration mode
        duration_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.duration_radio = ToggleButton(group='mode', state='down', size_hint_x=None, width=30, text='●')
        self.duration_radio.bind(on_press=self.on_duration_selected)
        duration_layout.add_widget(self.duration_radio)
        duration_layout.add_widget(Label(text='Play for hours/minutes/seconds:', size_hint_x=None, width=200))
        
        # Duration inputs
        duration_inputs = BoxLayout(orientation='horizontal', size_hint_x=None, width=300)
        duration_inputs.add_widget(Label(text='Hours:', size_hint_x=None, width=50))
        self.hours_input = TextInput(text='0', multiline=False, size_hint_x=None, width=60)
        duration_inputs.add_widget(self.hours_input)
        duration_inputs.add_widget(Label(text='Min:', size_hint_x=None, width=40))
        self.minutes_input = TextInput(text='30', multiline=False, size_hint_x=None, width=60)
        duration_inputs.add_widget(self.minutes_input)
        duration_inputs.add_widget(Label(text='Sec:', size_hint_x=None, width=40))
        self.seconds_input = TextInput(text='0', multiline=False, size_hint_x=None, width=60)
        duration_inputs.add_widget(self.seconds_input)
        duration_layout.add_widget(duration_inputs)
        mode_frame.add_widget(duration_layout)
        
        # Until mode
        until_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        self.until_radio = ToggleButton(group='mode', state='normal', size_hint_x=None, width=30, text='○')
        self.until_radio.bind(on_press=self.on_until_selected)
        until_layout.add_widget(self.until_radio)
        until_layout.add_widget(Label(text='Play until time (HH:MM):', size_hint_x=None, width=150))
        self.until_input = TextInput(text='22:30', multiline=False, size_hint_x=None, width=100)
        until_layout.add_widget(self.until_input)
        mode_frame.add_widget(until_layout)
        
        main_layout.add_widget(mode_frame)
        
        # Status section
        status_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=150)
        
        # Terraria status
        terraria_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        terraria_layout.add_widget(Label(text='Terraria Status:', size_hint_x=None, width=120))
        self.terraria_status = Label(text='Detecting...', size_hint_x=None, width=100)
        terraria_layout.add_widget(self.terraria_status)
        status_layout.add_widget(terraria_layout)
        
        # Remaining time
        remaining_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=30)
        remaining_layout.add_widget(Label(text='Remaining Time:', size_hint_x=None, width=120))
        self.remaining_label = Label(text='-', size_hint_x=None, width=100, font_size=16, bold=True)
        remaining_layout.add_widget(self.remaining_label)
        status_layout.add_widget(remaining_layout)
        
        # Progress bar
        progress_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=60)
        progress_layout.add_widget(Label(text='Progress:', size_hint_y=None, height=20))
        self.progress_bar = ProgressBar(max=1, value=0, size_hint_y=None, height=30)
        progress_layout.add_widget(self.progress_bar)
        status_layout.add_widget(progress_layout)
        
        main_layout.add_widget(status_layout)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        self.start_button = Button(text='Start', size_hint_x=0.3)
        self.start_button.bind(on_press=self.start_timer)
        button_layout.add_widget(self.start_button)
        
        self.stop_button = Button(text='Stop', size_hint_x=0.3)
        self.stop_button.bind(on_press=self.stop_timer)
        button_layout.add_widget(self.stop_button)
        
        self.exit_button = Button(text='Exit', size_hint_x=0.3)
        self.exit_button.bind(on_press=self.exit_app)
        button_layout.add_widget(self.exit_button)
        
        main_layout.add_widget(button_layout)
        
        self.add_widget(main_layout)
        
        # Schedule status updates
        Clock.schedule_interval(self.update_terraria_status, 1.0)
        
        # Store references for easy access (no need for custom ids object)

    def update_terraria_status(self, dt):
        """Update Terraria running status"""
        running = is_process_running(PROCESS_NAME)
        if running:
            self.terraria_status.text = "Running ✓"
            self.terraria_status.color = (0, 1, 0, 1)  # Green
        else:
            self.terraria_status.text = "Not detected ✗"
            self.terraria_status.color = (1, 0, 0, 1)  # Red

    def on_duration_selected(self, instance):
        """Handle duration mode selection"""
        self.duration_radio.state = 'down'
        self.until_radio.state = 'normal'
        self.duration_radio.text = '●'
        self.until_radio.text = '○'

    def on_until_selected(self, instance):
        """Handle until mode selection"""
        self.until_radio.state = 'down'
        self.duration_radio.state = 'normal'
        self.until_radio.text = '●'
        self.duration_radio.text = '○'

    def start_timer(self, instance):
        """Start the timer"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.show_popup("Error", "Timer is already running. Stop it first before starting a new one.")
            return

        # Compute planned_end
        session_start = now()
        if self.duration_radio.state == 'down':
            try:
                h = int(self.hours_input.text or "0")
                m = int(self.minutes_input.text or "0")
                s = int(self.seconds_input.text or "0")
                total = h*3600 + m*60 + s
            except ValueError:
                self.show_popup("Error", "Please enter valid integers for hours/minutes/seconds.")
                return
            if total <= 0:
                self.show_popup("Error", "Duration must be greater than 0.")
                return
            planned_end = session_start + dt.timedelta(seconds=total)
            mode_desc = f"Duration {h}h{m}m{s}s"
        else:
            t = parse_time_hhmm(self.until_input.text)
            if not t:
                self.show_popup("Error", "Please enter HH:MM (24-hour format), e.g., 22:30")
                return
            planned_end = dt.datetime.combine(session_start.date(), t)
            # If that time already passed today, assume tomorrow
            if planned_end <= session_start:
                planned_end += dt.timedelta(days=1)
            mode_desc = f"Until {planned_end.strftime('%H:%M')}"

        # Start monitor thread
        self.monitor_thread = MonitorThread(planned_end, mode_desc, session_start, App.get_running_app())
        self.monitor_thread.start()
        
        # Update UI
        remaining = int((planned_end - now()).total_seconds())
        self.ids.remaining_label.text = self.format_seconds(remaining)

    def stop_timer(self, instance):
        """Stop the timer"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
            self.monitor_thread = None
            self.ids.remaining_label.text = "Stopped"
            self.ids.progress_bar.value = 0
            self.show_popup("Info", "Timer stopped.")
        else:
            self.show_popup("Info", "No timer is currently running.")

    def exit_app(self, instance):
        """Exit the application"""
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.stop()
        App.get_running_app().stop()

    def format_seconds(self, sec: int) -> str:
        """Format seconds to HH:MM:SS or MM:SS"""
        m, s = divmod(sec, 60)
        h, m = divmod(m, 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def show_popup(self, title, message):
        """Show a popup message"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.6),
            auto_dismiss=True
        )
        popup.open()

class TerrariaTimekeeperApp(App):
    def build(self):
        """Build the application"""
        self.title = APP_NAME
        
        # Create screen manager
        sm = ScreenManager()
        
        # Add main screen
        main_screen = MainScreen(name='main')
        sm.add_widget(main_screen)
        
        return sm

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
    print("[OK] Kivy GUI framework")
    print("-" * 50)
    
    try:
        TerrariaTimekeeperApp().run()
    except Exception as e:
        print(f"Application error: {e}")
        input("Press Enter to exit...")

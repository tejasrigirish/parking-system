"""
Python Backend Server for Smart Parking System.
Provides a RESTful JSON API and serves the interactive HTML/CSS/JS frontend.
Zero external dependencies (uses Python standard library http.server).
"""

import http.server
import json
import urllib.parse
import os
import sys
import webbrowser
import socket
from datetime import datetime
from typing import Dict, Any

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from database import Database
from parking_manager import ParkingManager
import seed_data

WEB_DIR = os.path.join(BASE_DIR, "web")

db = Database()
manager = ParkingManager(db=db)

class ParkingRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        # Enable CORS and disable caching for development
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_HEAD(self):
        self.do_GET()

    def send_json(self, status_code: int, data: Dict[str, Any]):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def parse_json_body(self) -> Dict[str, Any]:
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                return {}
            body = self.rfile.read(content_length).decode("utf-8")
            return json.loads(body)
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # API Routes
        if path == "/api/slots":
            slots = db.get_all_slots()
            self.send_json(200, {"success": True, "slots": slots})
            return

        elif path == "/api/stats":
            stats = db.get_stats()
            next_slot = db.get_next_vacant_slot()
            stats["next_vacant_slot"] = next_slot
            self.send_json(200, {"success": True, "stats": stats})
            return

        elif path == "/api/active":
            raw_active = db.get_all_active_entries()
            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            active = []
            for item in raw_active:
                entry = dict(item)
                pricing = manager.calculate_pricing(entry["entry_time"], now_str)
                entry["duration"] = pricing["duration"]
                entry["duration_seconds"] = pricing["duration_seconds"]
                entry["duration_str"] = pricing["duration_str"]
                entry["current_amount"] = pricing["total_amount"]
                active.append(entry)
            self.send_json(200, {"success": True, "active_entries": active})
            return

        elif path == "/api/history":
            limit = int(query.get("limit", [100])[0])
            history = db.get_history(limit=limit)
            self.send_json(200, {"success": True, "history": history})
            return

        elif path == "/api/search":
            q = query.get("q", [""])[0].strip()
            if not q:
                self.send_json(400, {"success": False, "message": "Query parameter 'q' is required."})
                return
            ok, msg, record = manager.search_vehicle(q)
            self.send_json(200, {"success": ok, "message": msg, "data": record})
            return

        # Serve static web frontend
        if path == "/" or path == "":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/entry":
            payload = self.parse_json_body()
            vehicle_no = payload.get("vehicle_no", "").strip()
            if not vehicle_no:
                self.send_json(400, {"success": False, "message": "Vehicle number cannot be empty."})
                return
            ok, msg, details = manager.park_vehicle(vehicle_no)
            status_code = 200 if ok else 400
            self.send_json(status_code, {"success": ok, "message": msg, "details": details})
            return

        elif path == "/api/exit/preview":
            payload = self.parse_json_body()
            identifier = payload.get("identifier", "").strip()
            if not identifier:
                self.send_json(400, {"success": False, "message": "Vehicle plate or ticket number required."})
                return

            active = None
            if identifier.isdigit():
                active = db.get_active_entry_by_ticket(int(identifier))
            if not active:
                active = db.get_active_entry_by_vehicle(manager.normalize_vehicle_no(identifier))

            if not active:
                self.send_json(404, {"success": False, "message": "Vehicle not found or not currently parked."})
                return

            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            pricing = manager.calculate_pricing(active["entry_time"], now_str)
            response_data = {
                "ticket_no": active["ticket_no"],
                "vehicle_no": active["vehicle_no"],
                "slot_no": active["slot_no"],
                "entry_time": active["entry_time"],
                "preview_time": now_str,
                "duration": pricing["duration"],
                "current_amount": pricing["total_amount"],
                "pricing": pricing
            }
            self.send_json(200, {"success": True, "data": response_data})
            return

        elif path == "/api/exit":
            payload = self.parse_json_body()
            identifier = payload.get("identifier", "").strip()
            if not identifier:
                self.send_json(400, {"success": False, "message": "Vehicle plate or ticket number required."})
                return
            ok, msg, details = manager.exit_vehicle(identifier)
            status_code = 200 if ok else 400
            if ok and details:
                details["detailed_bill"] = manager.generate_detailed_exit_bill(details)
            self.send_json(status_code, {"success": ok, "message": msg, "details": details})
            return

        elif path == "/api/reset_seed":
            try:
                seed_data.seed_sample_data(reset=True)
                self.send_json(200, {"success": True, "message": "Database reset and seeded successfully!"})
            except Exception as e:
                self.send_json(500, {"success": False, "message": f"Seeding failed: {str(e)}"})
            return

        elif path == "/api/clear_data":
            try:
                db.clear_all_data(20)
                self.send_json(200, {"success": True, "message": "All data cleared! All 20 bays are now vacant."})
            except Exception as e:
                self.send_json(500, {"success": False, "message": f"Clearing failed: {str(e)}"})
            return

        self.send_json(404, {"success": False, "message": "Endpoint not found"})

def get_local_ip() -> str:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"

def find_free_port(start_port: int = 5000) -> int:
    port = start_port
    while port < 65535:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            res = sock.connect_ex(("127.0.0.1", port))
            if res != 0: # Port is available
                return port
            port += 1
    return start_port

def run_server(port: int = 5000, open_browser: bool = True):
    port = find_free_port(port)
    local_ip = get_local_ip()
    server_address = ("0.0.0.0", port)
    httpd = http.server.ThreadingHTTPServer(server_address, ParkingRequestHandler)
    local_url = f"http://localhost:{port}"
    network_url = f"http://{local_ip}:{port}"
    print(f"==================================================")
    print(f"  Park Wave Smart Parking Backend Running!")
    print(f"  --> On this device:    {local_url}")
    print(f"  --> On another device: {network_url} (same Wi-Fi)")
    print(f"==================================================")

    if open_browser:
        webbrowser.open(local_url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == "__main__":
    run_server(5000, open_browser=True)

"""
Modern Tkinter Desktop GUI for the Smart Parking System.
Features interactive visual parking slot grid, vehicle entry with duplicate validation,
exit billing calculator, vehicle search, database history, and printable receipt modal.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import os
import math
from typing import Optional, Dict, Any

from database import Database
from parking_manager import ParkingManager, BASE_FEE, HOURLY_RATE

class SmartParkingGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Park Wave - 4 Wheeler Smart Parking System (Bangalore)")
        self.root.geometry("1100x750")
        self.root.minsize(980, 650)
        self.root.configure(bg="#f1f5f9")

        # Core logic & DB instances
        self.db = Database()
        self.manager = ParkingManager(db=self.db)

        # Style configuration
        self.setup_styles()

        # Build UI layout
        self.build_header()
        self.build_kpi_bar()
        self.build_tabs()

        # Initial data load
        self.refresh_all()

        # Show BMW-style cinematic intro splash
        self.show_bmw_splash_intro()

    def show_bmw_splash_intro(self):
        splash = tk.Frame(self.root, bg="#050811")
        splash.place(relx=0, rely=0, relwidth=1, relheight=1)

        canvas = tk.Canvas(splash, bg="#050811", highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        skip_btn = tk.Button(
            splash,
            text="Skip ➜",
            font=("Segoe UI", 9, "bold"),
            bg="#1e293b",
            fg="#94a3b8",
            activebackground="#334155",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=lambda: self._dismiss_splash(splash)
        )
        skip_btn.place(relx=0.92, rely=0.92, anchor="center")

        cx = 550
        cy = 300
        radius = 75

        self._trace_angle = 0
        def trace_ring():
            if not splash.winfo_exists():
                return
            self._trace_angle += 14
            extent = min(359, self._trace_angle)
            canvas.delete("trace_arc")
            canvas.create_arc(
                cx - radius, cy - radius, cx + radius, cy + radius,
                start=90, extent=-extent,
                style="arc", outline="#e2e8f0", width=4, tags="trace_arc"
            )
            if self._trace_angle < 360:
                self.root.after(16, trace_ring)
            else:
                self.root.after(80, reveal_roundel)

        def reveal_roundel():
            if not splash.winfo_exists():
                return
            canvas.delete("trace_arc")
            # Outer dark shield with electric cyan rim
            canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, fill="#080c16", outline="#38bdf8", width=3)
            # Radar sensor guide tracks
            r_sensor = radius * 0.82
            canvas.create_oval(cx - r_sensor, cy - r_sensor, cx + r_sensor, cy + r_sensor, outline="#1e293b", width=1.5)

            # PARKWAVE Custom Monogram:
            # 1. Left Pillar of "P"
            p_w = 12
            p_h = radius * 1.1
            x_p = cx - radius * 0.35
            y_p = cy - radius * 0.55
            canvas.create_rectangle(x_p, y_p, x_p + p_w, y_p + p_h, fill="#ffffff", outline="#cbd5e1", width=1)

            # 2. Sweeping Aerodynamic Loop of "P"
            r_head = radius * 0.44
            canvas.create_arc(x_p, y_p - 4, x_p + r_head * 2, y_p + r_head * 2 - 4, start=-90, extent=180, fill="#0284c7", outline="#38bdf8", width=2)

            # 3. Dynamic Harmonic Wave Flute
            wave_y = cy + radius * 0.38
            canvas.create_line(cx - radius * 0.55, wave_y, cx - radius * 0.1, wave_y - 8, cx + radius * 0.35, wave_y + 6, cx + radius * 0.6, wave_y - 2, smooth=True, fill="#00f2fe", width=3)

            # 4. Smart Parking Pulse Beacon
            canvas.create_oval(x_p + r_head - 5, y_p + r_head - 9, x_p + r_head + 5, y_p + r_head + 1, fill="#38bdf8", outline="#ffffff", width=1.5)

            self.root.after(260, reveal_text)

        def reveal_text():
            if not splash.winfo_exists():
                return
            canvas.create_text(
                cx, cy + radius + 46,
                text="P A R K W A V E",
                font=("Segoe UI", 24, "bold"),
                fill="#ffffff"
            )
            canvas.create_text(
                cx, cy + radius + 82,
                text="SMART PARKING, SIMPLIFIED • BANGALORE",
                font=("Consolas", 10, "bold"),
                fill="#94a3b8"
            )
            self.root.after(1400, lambda: self._dismiss_splash(splash))

        splash.bind("<Button-1>", lambda e: self._dismiss_splash(splash))
        canvas.bind("<Button-1>", lambda e: self._dismiss_splash(splash))
        self.root.after(80, trace_ring)

    def _dismiss_splash(self, splash):
        if splash.winfo_exists():
            splash.destroy()

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Global font styles
        self.font_title = ("Segoe UI", 18, "bold")
        self.font_subtitle = ("Segoe UI", 10)
        self.font_heading = ("Segoe UI", 12, "bold")
        self.font_body = ("Segoe UI", 10)
        self.font_body_bold = ("Segoe UI", 10, "bold")
        self.font_mono = ("Consolas", 11)

        # Notebook tabs styling
        self.style.configure(
            "TNotebook",
            background="#f1f5f9",
            borderwidth=0
        )
        self.style.configure(
            "TNotebook.Tab",
            font=("Segoe UI", 11, "bold"),
            padding=[16, 8],
            background="#e2e8f0",
            foreground="#334155"
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", "#2563eb")],
            foreground=[("selected", "#ffffff")]
        )

        # Treeview styling
        self.style.configure(
            "Treeview",
            font=("Segoe UI", 10),
            rowheight=28,
            background="#ffffff",
            fieldbackground="#ffffff"
        )
        self.style.configure(
            "Treeview.Heading",
            font=("Segoe UI", 10, "bold"),
            background="#e2e8f0",
            foreground="#1e293b",
            padding=5
        )
        self.style.map("Treeview", background=[("selected", "#bfdbfe")], foreground=[("selected", "#1e3a8a")])

    def build_header(self):
        header_frame = tk.Frame(self.root, bg="#1e293b", height=70, padx=20, pady=12)
        header_frame.pack(fill="x", side="top")

        left_box = tk.Frame(header_frame, bg="#1e293b")
        left_box.pack(side="left")

        title_lbl = tk.Label(
            left_box,
            text="PARK WAVE • SMART PARKING SYSTEM",
            font=self.font_title,
            fg="#ffffff",
            bg="#1e293b"
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            left_box,
            text="Automated 4-Wheeler Slot Allocation, Duplicate Validation & Billing Engine • Bangalore",
            font=self.font_subtitle,
            fg="#94a3b8",
            bg="#1e293b"
        )
        sub_lbl.pack(anchor="w")

        # Refresh button
        refresh_btn = tk.Button(
            header_frame,
            text="↻ Refresh System",
            font=self.font_body_bold,
            bg="#3b82f6",
            fg="#ffffff",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=self.refresh_all
        )
        refresh_btn.pack(side="right")

    def build_kpi_bar(self):
        kpi_frame = tk.Frame(self.root, bg="#f1f5f9", padx=16, pady=10)
        kpi_frame.pack(fill="x")

        self.kpi_cards = {}
        metrics = [
            ("total_slots", "TOTAL CAPACITY", "20", "#0284c7"),
            ("occupied_slots", "OCCUPIED", "0", "#dc2626"),
            ("vacant_slots", "AVAILABLE VACANT", "20", "#16a34a"),
            ("total_revenue", "REVENUE COLLECTED", "Rs. 0.00", "#7c3aed"),
        ]

        for idx, (key, label, val, color) in enumerate(metrics):
            card = tk.Frame(kpi_frame, bg="#ffffff", bd=1, relief="solid", padx=15, pady=8)
            card.configure(highlightbackground="#cbd5e1", highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=6)

            lbl_title = tk.Label(card, text=label, font=("Segoe UI", 8, "bold"), fg="#64748b", bg="#ffffff")
            lbl_title.pack(anchor="w")

            lbl_val = tk.Label(card, text=val, font=("Segoe UI", 16, "bold"), fg=color, bg="#ffffff")
            lbl_val.pack(anchor="w")

            self.kpi_cards[key] = lbl_val

    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        # 1. Visual Slots Tab
        self.tab_grid = tk.Frame(self.notebook, bg="#ffffff", padx=16, pady=16)
        self.notebook.add(self.tab_grid, text=" 🅿 Visual Slot Grid ")
        self.setup_grid_tab()

        # 2. Vehicle Entry Tab
        self.tab_entry = tk.Frame(self.notebook, bg="#ffffff", padx=24, pady=20)
        self.notebook.add(self.tab_entry, text=" 🚗 Vehicle Entry ")
        self.setup_entry_tab()

        # 3. Vehicle Exit Tab
        self.tab_exit = tk.Frame(self.notebook, bg="#ffffff", padx=24, pady=20)
        self.notebook.add(self.tab_exit, text=" 💳 Vehicle Exit & Bill ")
        self.setup_exit_tab()

        # 4. Search Tab
        self.tab_search = tk.Frame(self.notebook, bg="#ffffff", padx=24, pady=20)
        self.notebook.add(self.tab_search, text=" 🔍 Search Vehicle ")
        self.setup_search_tab()

        # 5. History & Logs Tab
        self.tab_history = tk.Frame(self.notebook, bg="#ffffff", padx=16, pady=16)
        self.notebook.add(self.tab_history, text=" 📋 Records & History ")
        self.setup_history_tab()

    # -------------------------------------------------------------
    # TAB 1: Visual Slot Grid
    # -------------------------------------------------------------
    def setup_grid_tab(self):
        top_bar = tk.Frame(self.tab_grid, bg="#ffffff")
        top_bar.pack(fill="x", pady=(0, 12))

        lbl = tk.Label(
            top_bar,
            text="Real-Time Parking Bays (Click any occupied bay to quick-exit or inspect)",
            font=self.font_heading,
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl.pack(side="left")

        legend_box = tk.Frame(top_bar, bg="#ffffff")
        legend_box.pack(side="right")

        # Green legend
        tk.Label(legend_box, text="  ", bg="#22c55e", width=2).pack(side="left", padx=(10, 4))
        tk.Label(legend_box, text="Vacant", font=self.font_subtitle, bg="#ffffff", fg="#334155").pack(side="left")

        # Red legend
        tk.Label(legend_box, text="  ", bg="#ef4444", width=2).pack(side="left", padx=(15, 4))
        tk.Label(legend_box, text="Occupied", font=self.font_subtitle, bg="#ffffff", fg="#334155").pack(side="left")

        # Scrollable container for slots
        canvas = tk.Canvas(self.tab_grid, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.tab_grid, orient="vertical", command=canvas.yview)
        self.slots_inner_frame = tk.Frame(canvas, bg="#ffffff")

        self.slots_inner_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.slots_inner_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def render_slot_grid(self):
        for widget in self.slots_inner_frame.winfo_children():
            widget.destroy()

        slots = self.db.get_all_slots()
        cols = 5

        for index, slot in enumerate(slots):
            r = index // cols
            c = index % cols

            is_occupied = (slot["status"] == "Occupied")
            bg_color = "#fee2e2" if is_occupied else "#f0fdf4"
            border_color = "#f87171" if is_occupied else "#86efac"
            status_text = "OCCUPIED" if is_occupied else "VACANT"
            status_fg = "#b91c1c" if is_occupied else "#15803d"
            veh_text = slot["vehicle_no"] if slot["vehicle_no"] else "Available"

            card = tk.Frame(
                self.slots_inner_frame,
                bg=bg_color,
                highlightbackground=border_color,
                highlightthickness=2,
                padx=12,
                pady=10,
                width=170,
                height=110
            )
            card.grid(row=r, column=c, padx=8, pady=8, sticky="nsew")
            card.pack_propagate(False)

            # Slot header
            s_lbl = tk.Label(card, text=slot["slot_no"], font=("Segoe UI", 13, "bold"), fg="#0f172a", bg=bg_color)
            s_lbl.pack(anchor="w")

            # Status pill
            pill = tk.Label(
                card,
                text=f"● {status_text}",
                font=("Segoe UI", 9, "bold"),
                fg=status_fg,
                bg=bg_color
            )
            pill.pack(anchor="w", pady=(2, 4))

            # Vehicle Plate Box
            plate_bg = "#ffffff" if not is_occupied else "#1e293b"
            plate_fg = "#64748b" if not is_occupied else "#f8fafc"
            plate_lbl = tk.Label(
                card,
                text=veh_text,
                font=self.font_body_bold,
                bg=plate_bg,
                fg=plate_fg,
                relief="flat",
                padx=6,
                pady=2
            )
            plate_lbl.pack(fill="x", pady=(2, 0))

            # Click handler to interact with slot
            card.bind("<Button-1>", lambda e, s=slot: self.on_slot_clicked(s))
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, s=slot: self.on_slot_clicked(s))

    def on_slot_clicked(self, slot: Dict[str, Any]):
        if slot["status"] == "Occupied":
            v_no = slot["vehicle_no"]
            ans = messagebox.askyesno(
                "Slot Occupied",
                f"Slot {slot['slot_no']} is currently occupied by:\n\n"
                f"Vehicle: {v_no}\n\n"
                f"Would you like to proceed to Vehicle Exit & Billing for {v_no}?"
            )
            if ans:
                self.notebook.select(self.tab_exit)
                self.exit_input.delete(0, tk.END)
                self.exit_input.insert(0, v_no)
                self.preview_exit_bill()
        else:
            ans = messagebox.askyesno(
                "Slot Vacant",
                f"Slot {slot['slot_no']} is currently VACANT.\n\n"
                f"Would you like to register a new vehicle entry?"
            )
            if ans:
                self.notebook.select(self.tab_entry)
                self.entry_veh_input.focus_set()

    # -------------------------------------------------------------
    # TAB 2: Vehicle Entry
    # -------------------------------------------------------------
    def setup_entry_tab(self):
        container = tk.Frame(self.tab_entry, bg="#ffffff")
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#f8fafc", bd=1, relief="solid", padx=30, pady=25)
        card.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        card.pack(fill="x", pady=(0, 20))

        title = tk.Label(
            card,
            text="Park New 4-Wheeler Vehicle",
            font=self.font_heading,
            fg="#1e293b",
            bg="#f8fafc"
        )
        title.pack(anchor="w", pady=(0, 5))

        desc = tk.Label(
            card,
            text="The system will automatically perform duplicate validation and allot the next available vacant slot.",
            font=self.font_subtitle,
            fg="#64748b",
            bg="#f8fafc"
        )
        desc.pack(anchor="w", pady=(0, 15))

        input_frame = tk.Frame(card, bg="#f8fafc")
        input_frame.pack(fill="x")

        lbl_veh = tk.Label(
            input_frame,
            text="Vehicle Number Plate (e.g. KA 01 AB 1234):",
            font=self.font_body_bold,
            fg="#334155",
            bg="#f8fafc"
        )
        lbl_veh.pack(anchor="w", pady=(0, 4))

        self.entry_veh_input = tk.Entry(
            input_frame,
            font=("Segoe UI", 14),
            relief="solid",
            bd=1,
            fg="#0f172a",
            bg="#ffffff"
        )
        self.entry_veh_input.pack(fill="x", ipady=6, pady=(0, 15))
        self.entry_veh_input.bind("<Return>", lambda e: self.process_vehicle_entry())

        btn_park = tk.Button(
            card,
            text="✔ Allot Slot & Generate Entry Receipt",
            font=("Segoe UI", 11, "bold"),
            bg="#16a34a",
            fg="#ffffff",
            activebackground="#15803d",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.process_vehicle_entry
        )
        btn_park.pack(anchor="w")

        # Next Slot Indicator
        self.next_slot_lbl = tk.Label(
            card,
            text="Next Available Slot: Checking...",
            font=self.font_body_bold,
            fg="#2563eb",
            bg="#f8fafc"
        )
        self.next_slot_lbl.pack(anchor="w", pady=(12, 0))

    def process_vehicle_entry(self):
        vehicle_no = self.entry_veh_input.get().strip()
        if not vehicle_no:
            messagebox.showwarning("Input Required", "Please enter a vehicle number.")
            return

        ok, msg, details = self.manager.park_vehicle(vehicle_no)
        if not ok:
            # Displays exact required duplicate message
            messagebox.showerror("Entry Rejected", msg)
            return

        self.entry_veh_input.delete(0, tk.END)
        self.refresh_all()

        # Show Receipt Modal
        self.show_receipt_dialog(
            title="Park Wave - Entry Pass",
            receipt_text=details["receipt"],
            ticket_no=details["ticket_no"]
        )

    # -------------------------------------------------------------
    # TAB 3: Vehicle Exit & Billing
    # -------------------------------------------------------------
    def setup_exit_tab(self):
        container = tk.Frame(self.tab_exit, bg="#ffffff")
        container.pack(fill="both", expand=True)

        card = tk.Frame(container, bg="#f8fafc", bd=1, relief="solid", padx=30, pady=25)
        card.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        card.pack(fill="x", pady=(0, 20))

        title = tk.Label(
            card,
            text="Vehicle Exit & Billing Checkout",
            font=self.font_heading,
            fg="#1e293b",
            bg="#f8fafc"
        )
        title.pack(anchor="w", pady=(0, 5))

        desc = tk.Label(
            card,
            text="Pricing Rule: Base Fee ₹50 + ₹20/hr (Partial hours rounded up to next full hour).",
            font=self.font_subtitle,
            fg="#64748b",
            bg="#f8fafc"
        )
        desc.pack(anchor="w", pady=(0, 15))

        search_row = tk.Frame(card, bg="#f8fafc")
        search_row.pack(fill="x", pady=(0, 10))

        lbl_id = tk.Label(
            search_row,
            text="Enter Vehicle Number or Ticket No:",
            font=self.font_body_bold,
            fg="#334155",
            bg="#f8fafc"
        )
        lbl_id.pack(anchor="w", pady=(0, 4))

        action_box = tk.Frame(search_row, bg="#f8fafc")
        action_box.pack(fill="x")

        self.exit_input = tk.Entry(
            action_box,
            font=("Segoe UI", 13),
            relief="solid",
            bd=1,
            fg="#0f172a",
            bg="#ffffff"
        )
        self.exit_input.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        self.exit_input.bind("<Return>", lambda e: self.preview_exit_bill())

        btn_calc = tk.Button(
            action_box,
            text="🔍 Calculate Bill",
            font=self.font_body_bold,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=16,
            pady=6,
            cursor="hand2",
            command=self.preview_exit_bill
        )
        btn_calc.pack(side="left")

        # Bill Preview Frame
        self.bill_preview_frame = tk.Frame(card, bg="#ffffff", bd=1, relief="solid", padx=20, pady=15)
        self.bill_preview_frame.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        self.bill_preview_frame.pack(fill="x", pady=(15, 15))

        self.bill_labels = {}
        fields = [
            ("veh", "Vehicle Number:"),
            ("slot", "Allocated Slot:"),
            ("entry", "Entry Timestamp:"),
            ("duration", "Parked Duration:"),
            ("hours", "Billed Hours (ceil):"),
            ("base", "Base Fee (Flat):"),
            ("hourly", "Hourly Fee (₹20/hr):"),
            ("total", "Total Amount to Pay:"),
        ]

        for k, label in fields:
            row = tk.Frame(self.bill_preview_frame, bg="#ffffff")
            row.pack(fill="x", pady=2)
            lbl_k = tk.Label(row, text=label, font=self.font_body, fg="#475569", bg="#ffffff", width=22, anchor="w")
            lbl_k.pack(side="left")

            fg_val = "#dc2626" if k == "total" else "#0f172a"
            font_val = ("Segoe UI", 12, "bold") if k == "total" else self.font_body_bold
            lbl_v = tk.Label(row, text="---", font=font_val, fg=fg_val, bg="#ffffff", anchor="w")
            lbl_v.pack(side="left")
            self.bill_labels[k] = lbl_v

        # Checkout Button
        self.btn_confirm_exit = tk.Button(
            card,
            text="✔ Confirm Exit, Collect Payment & Generate Final Receipt",
            font=("Segoe UI", 11, "bold"),
            bg="#dc2626",
            fg="#ffffff",
            activebackground="#b91c1c",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            state="disabled",
            command=self.execute_vehicle_exit
        )
        self.btn_confirm_exit.pack(anchor="w")

    def preview_exit_bill(self):
        target = self.exit_input.get().strip()
        if not target:
            messagebox.showwarning("Input Required", "Please enter a vehicle number or ticket number.")
            return

        # Find active entry
        active_entry = None
        if target.isdigit():
            active_entry = self.db.get_active_entry_by_ticket(int(target))
        if not active_entry:
            active_entry = self.db.get_active_entry_by_vehicle(self.manager.normalize_vehicle_no(target))

        if not active_entry:
            messagebox.showerror("Not Found", "Vehicle not found or not currently parked")
            self.btn_confirm_exit.configure(state="disabled")
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pricing = self.manager.calculate_pricing(active_entry["entry_time"], now_str)

        self.bill_labels["veh"].configure(text=active_entry["vehicle_no"])
        self.bill_labels["slot"].configure(text=active_entry["slot_no"])
        self.bill_labels["entry"].configure(text=active_entry["entry_time"])
        self.bill_labels["duration"].configure(text=pricing["duration_str"])
        self.bill_labels["hours"].configure(text=f"{pricing['billed_hours']} hr(s) (1 base + {pricing['additional_hours']} addl)")
        self.bill_labels["base"].configure(text=f"Rs. {pricing['base_fee']:.2f} (1st hour)")
        self.bill_labels["hourly"].configure(text=f"Rs. {pricing['hourly_charge']:.2f} ({pricing['additional_hours']} × ₹20)")
        self.bill_labels["total"].configure(text=f"Rs. {pricing['total_amount']:.2f}")

        self.btn_confirm_exit.configure(state="normal")
        self.current_exit_target = target

    def execute_vehicle_exit(self):
        if not hasattr(self, "current_exit_target") or not self.current_exit_target:
            return

        ok, msg, details = self.manager.exit_vehicle(self.current_exit_target)
        if not ok:
            messagebox.showerror("Exit Failed", msg)
            return

        self.btn_confirm_exit.configure(state="disabled")
        self.exit_input.delete(0, tk.END)
        for lbl in self.bill_labels.values():
            lbl.configure(text="---")

        self.refresh_all()

        # Detailed Exit Bill Modal
        detailed_bill = self.manager.generate_detailed_exit_bill(details)
        self.show_receipt_dialog(
            title="Park Wave - Final Bill & Receipt",
            receipt_text=detailed_bill,
            ticket_no=details["ticket_no"]
        )

    # -------------------------------------------------------------
    # TAB 4: Search Vehicle
    # -------------------------------------------------------------
    def setup_search_tab(self):
        card = tk.Frame(self.tab_search, bg="#f8fafc", bd=1, relief="solid", padx=30, pady=25)
        card.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        card.pack(fill="x", pady=(0, 20))

        title = tk.Label(
            card,
            text="Search Currently Parked Vehicle",
            font=self.font_heading,
            fg="#1e293b",
            bg="#f8fafc"
        )
        title.pack(anchor="w", pady=(0, 15))

        search_box = tk.Frame(card, bg="#f8fafc")
        search_box.pack(fill="x", pady=(0, 15))

        self.search_input = tk.Entry(
            search_box,
            font=("Segoe UI", 13),
            relief="solid",
            bd=1,
            fg="#0f172a",
            bg="#ffffff"
        )
        self.search_input.pack(side="left", fill="x", expand=True, ipady=5, padx=(0, 10))
        self.search_input.bind("<Return>", lambda e: self.execute_search())

        btn_search = tk.Button(
            search_box,
            text="🔍 Search Vehicle",
            font=self.font_body_bold,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=18,
            pady=6,
            cursor="hand2",
            command=self.execute_search
        )
        btn_search.pack(side="left")

        # Search Result Card
        self.search_res_frame = tk.Frame(card, bg="#ffffff", bd=1, relief="solid", padx=20, pady=15)
        self.search_res_frame.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        self.search_res_frame.pack(fill="x")

        self.search_res_lbl = tk.Label(
            self.search_res_frame,
            text="Enter a vehicle number above to check slot allocation and live parked duration.",
            font=self.font_body,
            fg="#64748b",
            bg="#ffffff"
        )
        self.search_res_lbl.pack(anchor="w")

    def execute_search(self):
        query = self.search_input.get().strip()
        if not query:
            messagebox.showwarning("Input Required", "Please enter a vehicle number.")
            return

        ok, msg, res = self.manager.search_vehicle(query)
        if not ok:
            self.search_res_lbl.configure(
                text=f"❌ {msg}",
                font=self.font_body_bold,
                fg="#dc2626"
            )
            return

        res_text = (
            f"✔ Vehicle Found!\n\n"
            f"  • Vehicle Plate  : {res['vehicle_no']}\n"
            f"  • Allocated Slot : {res['slot_no']}\n"
            f"  • Ticket Number  : #{res['ticket_no']}\n"
            f"  • Entry Time     : {res['entry_time']}\n"
            f"  • Parked Duration: {res.get('current_duration', 'N/A')}\n"
            f"  • Est. Amount Due: Rs. {res.get('estimated_amount', 50.0):.2f}"
        )
        self.search_res_lbl.configure(
            text=res_text,
            font=self.font_body,
            fg="#0f172a"
        )

    # -------------------------------------------------------------
    # TAB 5: Records & History
    # -------------------------------------------------------------
    def setup_history_tab(self):
        top_row = tk.Frame(self.tab_history, bg="#ffffff")
        top_row.pack(fill="x", pady=(0, 10))

        lbl = tk.Label(
            top_row,
            text="Vehicle Entries & Parking History Log",
            font=self.font_heading,
            fg="#1e293b",
            bg="#ffffff"
        )
        lbl.pack(side="left")

        # Treeview Table
        tree_frame = tk.Frame(self.tab_history, bg="#ffffff")
        tree_frame.pack(fill="both", expand=True)

        cols = ("ticket", "vehicle", "slot", "entry", "exit", "amount", "status")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="browse")

        self.tree.heading("ticket", text="Ticket No")
        self.tree.heading("vehicle", text="Vehicle Number")
        self.tree.heading("slot", text="Slot No")
        self.tree.heading("entry", text="Entry Timestamp")
        self.tree.heading("exit", text="Exit Timestamp")
        self.tree.heading("amount", text="Amount Paid")
        self.tree.heading("status", text="Session Status")

        self.tree.column("ticket", width=90, anchor="center")
        self.tree.column("vehicle", width=140, anchor="center")
        self.tree.column("slot", width=90, anchor="center")
        self.tree.column("entry", width=180, anchor="center")
        self.tree.column("exit", width=180, anchor="center")
        self.tree.column("amount", width=120, anchor="center")
        self.tree.column("status", width=120, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")

    def refresh_history(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        records = self.db.get_history(limit=150)
        for r in records:
            status = "COMPLETED" if r["exit_time"] else "ACTIVE"
            exit_display = r["exit_time"] if r["exit_time"] else "---"
            amount_display = f"Rs. {r['amount']:.2f}" if r["amount"] is not None else "Active"

            self.tree.insert(
                "",
                "end",
                values=(
                    f"#{r['ticket_no']}",
                    r["vehicle_no"],
                    r["slot_no"],
                    r["entry_time"],
                    exit_display,
                    amount_display,
                    status
                )
            )

    # -------------------------------------------------------------
    # Shared Data Refresh & Receipt Dialog
    # -------------------------------------------------------------
    def refresh_all(self):
        stats = self.db.get_stats()
        self.kpi_cards["total_slots"].configure(text=str(stats["total_slots"]))
        self.kpi_cards["occupied_slots"].configure(text=str(stats["occupied_slots"]))
        self.kpi_cards["vacant_slots"].configure(text=str(stats["vacant_slots"]))
        self.kpi_cards["total_revenue"].configure(text=f"Rs. {stats['total_revenue']:.2f}")

        next_slot = self.db.get_next_vacant_slot()
        next_text = f"Next Available Slot: {next_slot}" if next_slot else "Next Available Slot: FULL"
        self.next_slot_lbl.configure(text=next_text)

        self.render_slot_grid()
        self.refresh_history()

    def show_receipt_dialog(self, title: str, receipt_text: str, ticket_no: int):
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("460x480")
        dialog.resizable(False, False)
        dialog.configure(bg="#f8fafc", padx=20, pady=20)
        dialog.transient(self.root)
        dialog.grab_set()

        # Receipt Card
        card = tk.Frame(dialog, bg="#ffffff", bd=1, relief="solid", padx=15, pady=15)
        card.configure(highlightbackground="#cbd5e1", highlightthickness=1)
        card.pack(fill="both", expand=True, pady=(0, 15))

        txt = tk.Text(card, font=self.font_mono, bg="#ffffff", fg="#0f172a", relief="flat", wrap="word")
        txt.insert("1.0", receipt_text)
        txt.configure(state="disabled")
        txt.pack(fill="both", expand=True)

        btn_box = tk.Frame(dialog, bg="#f8fafc")
        btn_box.pack(fill="x")

        def save_to_file():
            default_fn = f"receipt_ticket_{ticket_no}.txt"
            fpath = filedialog.asksaveasfilename(
                parent=dialog,
                initialfile=default_fn,
                defaultextension=".txt",
                filetypes=[("Text File", "*.txt"), ("All Files", "*.*")]
            )
            if fpath:
                try:
                    with open(fpath, "w", encoding="utf-8") as f:
                        f.write(receipt_text)
                    messagebox.showinfo("Saved", f"Receipt saved successfully to:\n{fpath}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save file: {e}")

        btn_save = tk.Button(
            btn_box,
            text="💾 Save Receipt (.txt)",
            font=self.font_body_bold,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=save_to_file
        )
        btn_save.pack(side="left")

        btn_close = tk.Button(
            btn_box,
            text="Close",
            font=self.font_body,
            bg="#e2e8f0",
            fg="#334155",
            activebackground="#cbd5e1",
            relief="flat",
            padx=14,
            pady=6,
            cursor="hand2",
            command=dialog.destroy
        )
        btn_close.pack(side="right")

def run_app():
    root = tk.Tk()
    app = SmartParkingGUI(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()

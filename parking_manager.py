"""
Core business logic for the Smart Parking System.
Handles duplicate checks, slot allocations, pricing calculation, exit workflows, and receipt generation.
"""

from datetime import datetime
import math
from typing import Optional, Dict, Tuple, Any
from database import Database

# Pricing Constants
BASE_FEE = 50.0       # Base entry fee in INR (covers first 1 hour)
HOURLY_RATE = 20.0    # Additional charge per started hour after first hour in INR

def calculate_fee(entry_time: Any, current_time: Optional[Any] = None) -> float:
    """
    Centralized fee-calculation function:
    Calculate parking fee strictly according to actual elapsed parking time.
    Pricing Rules:
    - Base fare: ₹50 (covers the first 1 hour only)
    - If duration <= 1 hour: Amount = ₹50
    - If duration > 1 hour:
        Additional Hours = ceil(duration_in_hours - 1)
        Amount = ₹50 + (Additional Hours × ₹20)
    - ₹20 must NOT be added before the first complete hour has elapsed.
    """
    dt_format = "%Y-%m-%d %H:%M:%S"
    if isinstance(entry_time, str):
        entry_dt = datetime.strptime(entry_time, dt_format)
    elif isinstance(entry_time, datetime):
        entry_dt = entry_time
    else:
        raise ValueError(f"Unsupported entry_time type: {type(entry_time)}")

    if current_time is None:
        current_dt = datetime.now()
    elif isinstance(current_time, str):
        current_dt = datetime.strptime(current_time, dt_format)
    elif isinstance(current_time, datetime):
        current_dt = current_time
    else:
        raise ValueError(f"Unsupported current_time type: {type(current_time)}")

    delta_seconds = (current_dt - entry_dt).total_seconds()
    if delta_seconds < 0:
        delta_seconds = 0.0

    # First hour rule: 3600 seconds covered by base fare
    if delta_seconds <= 3600.0:
        return float(BASE_FEE)
    else:
        extra_seconds = delta_seconds - 3600.0
        additional_hours = math.ceil(extra_seconds / 3600.0)
        return float(BASE_FEE + (additional_hours * HOURLY_RATE))

class ParkingManager:
    def __init__(self, db: Optional[Database] = None):
        self.db = db if db is not None else Database()

    @staticmethod
    def calculate_fee(entry_time: Any, current_time: Optional[Any] = None) -> float:
        """Centralized calculate_fee static method on ParkingManager."""
        return calculate_fee(entry_time, current_time)

    @staticmethod
    def normalize_vehicle_no(vehicle_no: str) -> str:
        """Strip extra spaces and convert to uppercase."""
        if not vehicle_no:
            return ""
        # Collapse multiple spaces into single space and capitalize
        return " ".join(vehicle_no.strip().upper().split())

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to a human-friendly string (e.g., '2h 15m')."""
        total_seconds = int(max(0, seconds))
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0 or days > 0:
            parts.append(f"{hours}h")
        parts.append(f"{minutes}m")
        if not parts or (days == 0 and hours == 0 and minutes == 0):
            parts.append(f"{secs}s")
        return " ".join(parts)

    def calculate_pricing(self, entry_time: Any, exit_time: Optional[Any] = None) -> Dict[str, Any]:
        """
        Calculate parking fee based on the system rules:
        - Base fare: ₹50 (covers first 1 hour only)
        - If duration <= 1 hour: Amount = ₹50
        - If duration > 1 hour:
            Additional Hours = ceil(duration_in_hours - 1)
            Amount = ₹50 + (Additional Hours × ₹20)
        - ₹20 must NOT be added before the first complete hour has elapsed.
        """
        dt_format = "%Y-%m-%d %H:%M:%S"
        if isinstance(entry_time, str):
            entry_dt = datetime.strptime(entry_time, dt_format)
            entry_time_str = entry_time
        else:
            entry_dt = entry_time
            entry_time_str = entry_dt.strftime(dt_format)

        if exit_time is None:
            exit_dt = datetime.now()
            exit_time_str = exit_dt.strftime(dt_format)
        elif isinstance(exit_time, str):
            exit_dt = datetime.strptime(exit_time, dt_format)
            exit_time_str = exit_time
        else:
            exit_dt = exit_time
            exit_time_str = exit_dt.strftime(dt_format)

        delta_seconds = (exit_dt - entry_dt).total_seconds()
        if delta_seconds < 0:
            delta_seconds = 0.0

        if delta_seconds <= 3600.0:
            additional_hours = 0
            billed_hours = 1
            hourly_charge = 0.0
            total_amount = float(BASE_FEE)
        else:
            extra_seconds = delta_seconds - 3600.0
            additional_hours = math.ceil(extra_seconds / 3600.0)
            billed_hours = 1 + additional_hours
            hourly_charge = float(additional_hours * HOURLY_RATE)
            total_amount = float(BASE_FEE + hourly_charge)

        duration_hours = round(delta_seconds / 3600.0, 2)

        return {
            "entry_time": entry_time_str,
            "exit_time": exit_time_str,
            "duration_seconds": delta_seconds,
            "duration_hours": duration_hours,
            "duration": duration_hours,
            "duration_str": self.format_duration(delta_seconds),
            "billed_hours": billed_hours,
            "additional_hours": additional_hours,
            "base_fee": BASE_FEE,
            "hourly_rate": HOURLY_RATE,
            "hourly_charge": hourly_charge,
            "total_amount": total_amount,
            "current_amount": total_amount,
        }

    def park_vehicle(self, vehicle_no: str, custom_entry_time: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Register vehicle entry:
        1. Validates vehicle number format.
        2. Duplicate Check: Checks if vehicle already exists among currently active parked entries.
           - If it exists -> returns "Invalid entry, the vehicle already exists"
        3. Finds next vacant slot.
           - If none -> returns "Parking full: No vacant slots available"
        4. Atomically marks slot as Occupied and logs vehicle entry.
        5. Returns entry details with provisional receipt.
        """
        clean_vehicle = self.normalize_vehicle_no(vehicle_no)
        if not clean_vehicle:
            return False, "Vehicle number cannot be empty.", None

        # 1. DUPLICATE CHECK: Verify if vehicle is already parked
        active_entry = self.db.get_active_entry_by_vehicle(clean_vehicle)
        if active_entry:
            return False, "Invalid entry, the vehicle already exists", None

        # 2. Find next vacant slot
        slot_no = self.db.get_next_vacant_slot()
        if not slot_no:
            return False, "Parking full: No vacant slots available", None

        # 3. Timestamp
        entry_time = custom_entry_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 4. Allocate slot and persist entry
        try:
            ticket_no = self.db.allocate_slot_and_create_entry(clean_vehicle, slot_no, entry_time)
        except Exception as e:
            return False, f"Allocation error: {str(e)}", None

        entry_details = {
            "ticket_no": ticket_no,
            "vehicle_no": clean_vehicle,
            "slot_no": slot_no,
            "entry_time": entry_time,
            "base_fee": BASE_FEE,
        }
        receipt = self.generate_entry_receipt(entry_details)
        entry_details["receipt"] = receipt

        return True, f"Vehicle {clean_vehicle} parked successfully at slot {slot_no}.", entry_details

    def exit_vehicle(self, identifier: str, custom_exit_time: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Process vehicle exit by vehicle number or ticket number:
        1. Finds active entry.
        2. Calculates parked duration and total amount due.
        3. Frees the slot (status = 'Vacant') and updates vehicle_entries record.
        4. Generates final exit receipt.
        """
        clean_id = str(identifier).strip()
        if not clean_id:
            return False, "Please provide a valid vehicle number or ticket number.", None

        # Look up active entry
        active_entry = None
        if clean_id.isdigit():
            active_entry = self.db.get_active_entry_by_ticket(int(clean_id))
        
        if not active_entry:
            clean_vehicle = self.normalize_vehicle_no(clean_id)
            active_entry = self.db.get_active_entry_by_vehicle(clean_vehicle)

        if not active_entry:
            return False, "Vehicle not found or not currently parked", None

        ticket_no = active_entry["ticket_no"]
        vehicle_no = active_entry["vehicle_no"]
        slot_no = active_entry["slot_no"]
        entry_time = active_entry["entry_time"]

        exit_time = custom_exit_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Calculate pricing
        pricing = self.calculate_pricing(entry_time, exit_time)
        total_amount = pricing["total_amount"]

        # Complete exit in database
        success = self.db.complete_exit(ticket_no, slot_no, exit_time, total_amount)
        if not success:
            return False, "Failed to complete exit in database.", None

        exit_details = {
            "ticket_no": ticket_no,
            "vehicle_no": vehicle_no,
            "slot_no": slot_no,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "duration": pricing["duration"],
            "duration_str": pricing["duration_str"],
            "billed_hours": pricing["billed_hours"],
            "additional_hours": pricing["additional_hours"],
            "base_fee": pricing["base_fee"],
            "hourly_charge": pricing["hourly_charge"],
            "amount": total_amount,
        }

        receipt = self.generate_exit_receipt(exit_details)
        exit_details["receipt"] = receipt

        return True, f"Vehicle {vehicle_no} exited successfully from slot {slot_no}.", exit_details

    def search_vehicle(self, vehicle_no: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        Search for a vehicle currently parked:
        - If parked: returns slot number, entry time, ticket number, live duration, and live amount.
        - If not parked: returns "Vehicle not found or not currently parked".
        """
        clean_vehicle = self.normalize_vehicle_no(vehicle_no)
        if not clean_vehicle:
            return False, "Please enter a vehicle number to search.", None

        record = self.db.search_vehicle(clean_vehicle)
        if not record:
            return False, "Vehicle not found or not currently parked", None

        # Compute current real-time elapsed duration and fee
        try:
            entry_dt = datetime.strptime(record["entry_time"], "%Y-%m-%d %H:%M:%S")
            now_dt = datetime.now()
            now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
            pricing = self.calculate_pricing(record["entry_time"], now_str)
            record["current_duration"] = pricing["duration_str"]
            record["duration"] = pricing["duration"]
            record["estimated_amount"] = pricing["total_amount"]
            record["current_amount"] = pricing["total_amount"]
        except Exception:
            record["current_duration"] = "N/A"
            record["duration"] = 0.0
            record["estimated_amount"] = BASE_FEE
            record["current_amount"] = BASE_FEE

        return True, f"Vehicle {clean_vehicle} is parked in slot {record['slot_no']}.", record

    def generate_entry_receipt(self, details: Dict[str, Any]) -> str:
        """
        Generate entry pass matching the required receipt layout:
                Park Wave - 4 Wheeler Parking
                        Bangalore
        ----------------------------------------
        Ticket No   : <serial no / ticket number>
        Vehicle No  : <vehicle number>
        Entry Time  : <date & time>
        Slot No     : <allocated slot>
        ----------------------------------------
        Amount to Pay: ₹<amount>
        ----------------------------------------
              Thank you, visit again!
        """
        amount_str = f"{details.get('base_fee', BASE_FEE):.2f}"
        receipt = (
            "        Park Wave - 4 Wheeler Parking\n"
            "                Bangalore\n"
            "----------------------------------------\n"
            f"Ticket No   : {details['ticket_no']}\n"
            f"Vehicle No  : {details['vehicle_no']}\n"
            f"Entry Time  : {details['entry_time']}\n"
            f"Slot No     : {details['slot_no']}\n"
            "----------------------------------------\n"
            f"Amount to Pay: ₹{amount_str} (Base Fee)\n"
            "----------------------------------------\n"
            "      Thank you, visit again!"
        )
        return receipt

    def generate_exit_receipt(self, details: Dict[str, Any]) -> str:
        """
        Generate final exit receipt:
        Park Wave - 4 Wheeler Parking, Bangalore

        Ticket No        : <serial no / ticket number>
        Vehicle No       : <vehicle number>
        Slot             : <allocated slot>
        Entry Time       : <date & time>
        Exit Time        : <date & time>
        Total Duration   : <duration string>
        ----------------------------------------
        Total Amount Paid: ₹<amount>
        """
        amount_val = details.get('amount', 0.0)
        amount_str = f"{amount_val:.2f}"
        exit_time_str = details.get('exit_time', 'N/A')
        duration_str = details.get('duration_str', 'N/A')
        receipt = (
            "Park Wave - 4 Wheeler Parking, Bangalore\n"
            "----------------------------------------\n"
            f"Ticket No        : {details['ticket_no']}\n"
            f"Vehicle No       : {details['vehicle_no']}\n"
            f"Slot             : {details['slot_no']}\n"
            f"Entry Time       : {details['entry_time']}\n"
            f"Exit Time        : {exit_time_str}\n"
            f"Total Duration   : {duration_str}\n"
            "----------------------------------------\n"
            f"Total Amount Paid: ₹{amount_str}\n"
            "----------------------------------------\n"
            "        Thank you, visit again!"
        )
        return receipt

    def generate_detailed_exit_bill(self, details: Dict[str, Any]) -> str:
        """
        Generate an extended itemized invoice showing exact parking duration,
        base fee (covering 1st hour), and additional hourly charges.
        """
        amount_val = details.get('amount', 0.0)
        base_fee = details.get('base_fee', BASE_FEE)
        hourly_charge = details.get('hourly_charge', 0.0)
        billed_hours = details.get('billed_hours', 1)
        additional_hours = details.get('additional_hours', max(0, billed_hours - 1))
        duration_str = details.get('duration_str', 'N/A')

        receipt = (
            "========================================\n"
            "Park Wave - 4 Wheeler Parking, Bangalore\n"
            "         TAX INVOICE / RECEIPT          \n"
            "========================================\n"
            f"Ticket No        : {details['ticket_no']}\n"
            f"Vehicle No       : {details['vehicle_no']}\n"
            f"Slot             : {details['slot_no']}\n"
            f"Entry Time       : {details['entry_time']}\n"
            f"Exit Time        : {details.get('exit_time', 'N/A')}\n"
            f"Total Duration   : {duration_str}\n"
            f"Billed Hours     : {billed_hours} hr(s) (1 base + {additional_hours} addl)\n"
            "----------------------------------------\n"
            f"Base Fare (1 hr)       : ₹{base_fee:6.2f}\n"
            f"Addl Fee ({additional_hours} × ₹20)     : ₹{hourly_charge:6.2f}\n"
            "----------------------------------------\n"
            f"Total Amount Paid      : ₹{amount_val:6.2f}\n"
            "========================================\n"
            "        Thank you, visit again!         \n"
            "========================================"
        )
        return receipt

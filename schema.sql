-- ====================================================================
-- Smart Parking System Database Schema
-- DBMS: SQLite / MySQL compatible
-- Park Wave - 4 Wheeler Parking, Bangalore
-- ====================================================================

-- 1. Parking Slots Table
-- Keeps track of the physical parking slots, occupancy status, and current vehicle
CREATE TABLE IF NOT EXISTS parking_slots (
    slot_no TEXT PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('Occupied', 'Vacant')),
    vehicle_no TEXT DEFAULT NULL
);

-- 2. Vehicle Entries Table
-- Keeps track of all historical and active parking sessions
CREATE TABLE IF NOT EXISTS vehicle_entries (
    ticket_no INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_no TEXT NOT NULL,
    slot_no TEXT NOT NULL,
    entry_time TEXT NOT NULL,
    exit_time TEXT DEFAULT NULL,
    amount REAL DEFAULT NULL,
    FOREIGN KEY (slot_no) REFERENCES parking_slots(slot_no)
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_entries_vehicle_active 
ON vehicle_entries (vehicle_no, exit_time);

CREATE INDEX IF NOT EXISTS idx_slots_status 
ON parking_slots (status);

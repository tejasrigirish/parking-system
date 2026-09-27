/**
 * Park Wave - Frontend Logic & API Integration
 * Connects the interactive UI with the Python REST backend.
 */

const API_BASE = ""; // Relative to server root

// Global App State
const state = {
  slots: [],
  stats: {},
  activeEntries: [],
  history: [],
  currentReceipt: {
    text: "",
    ticketNo: 1,
  },
  currentFilter: "all",
};

// DOM Element Selectors
const DOM = {
  liveClock: document.getElementById("liveClock"),
  btnClearData: document.getElementById("btnClearData"),

  // KPIs
  kpiTotal: document.getElementById("kpiTotal"),
  kpiOccupied: document.getElementById("kpiOccupied"),
  kpiVacant: document.getElementById("kpiVacant"),
  kpiRevenue: document.getElementById("kpiRevenue"),
  kpiNextSlot: document.getElementById("kpiNextSlot"),

  // Tabs
  tabButtons: document.querySelectorAll(".tab-btn"),
  tabContents: document.querySelectorAll(".tab-content"),

  // Grid
  slotsGrid: document.getElementById("slotsGrid"),
  filterButtons: document.querySelectorAll(".filter-btn"),
  btnRefreshGrid: document.getElementById("btnRefreshGrid"),

  // Entry
  formEntry: document.getElementById("formEntry"),
  inputVehicleNo: document.getElementById("inputVehicleNo"),
  entryPreviewSlot: document.getElementById("entryPreviewSlot"),
  entryErrorAlert: document.getElementById("entryErrorAlert"),
  entryErrorMessage: document.getElementById("entryErrorMessage"),

  // Exit
  selectActiveVehicle: document.getElementById("selectActiveVehicle"),
  inputExitTarget: document.getElementById("inputExitTarget"),
  btnPreviewBill: document.getElementById("btnPreviewBill"),
  btnConfirmExit: document.getElementById("btnConfirmExit"),
  billVehicle: document.getElementById("billVehicle"),
  billSlot: document.getElementById("billSlot"),
  billEntryTime: document.getElementById("billEntryTime"),
  billExitTime: document.getElementById("billExitTime"),
  billDuration: document.getElementById("billDuration"),
  billBilledHours: document.getElementById("billBilledHours"),
  billHourlyCharge: document.getElementById("billHourlyCharge"),
  billTotalAmount: document.getElementById("billTotalAmount"),
  billStatus: document.getElementById("billStatus"),

  // Search
  searchQueryInput: document.getElementById("searchQueryInput"),
  btnSearchVehicle: document.getElementById("btnSearchVehicle"),
  searchResultContainer: document.getElementById("searchResultContainer"),
  searchNotFoundAlert: document.getElementById("searchNotFoundAlert"),
  searchResultSlot: document.getElementById("searchResultSlot"),
  searchResultPlate: document.getElementById("searchResultPlate"),
  searchResultTicket: document.getElementById("searchResultTicket"),
  searchResultEntry: document.getElementById("searchResultEntry"),
  searchResultDuration: document.getElementById("searchResultDuration"),
  searchResultAmount: document.getElementById("searchResultAmount"),
  btnGoToSlot: document.getElementById("btnGoToSlot"),

  // History & Ledger
  historyTableBody: document.getElementById("historyTableBody"),
  ledgerFilterInput: document.getElementById("ledgerFilterInput"),
  btnExportCsv: document.getElementById("btnExportCsv"),
  btnRefreshHistory: document.getElementById("btnRefreshHistory"),

  // Receipt Dialog
  receiptDialog: document.getElementById("receiptDialog"),
  receiptDialogTitle: document.getElementById("receiptDialogTitle"),
  receiptContent: document.getElementById("receiptContent"),
  receiptBarcode: document.getElementById("receiptBarcode"),
  btnDownloadReceipt: document.getElementById("btnDownloadReceipt"),
  btnPrintReceipt: document.getElementById("btnPrintReceipt"),
  btnCloseReceipt: document.getElementById("btnCloseReceipt"),
  btnDismissReceipt: document.getElementById("btnDismissReceipt"),

  // Toast
  toastContainer: document.getElementById("toastContainer"),

  // Cinematic Animated Background
  btnToggleCinema: document.getElementById("btnToggleCinema"),
  cinemaToggleText: document.getElementById("cinemaToggleText"),
  cinemaLotBg: document.getElementById("cinemaLotBg"),
  cinemaParallax: document.getElementById("cinemaParallax"),
  cinemaLotBeacons: document.getElementById("cinemaLotBeacons"),
  cinemaCarsStage: document.getElementById("cinemaCarsStage"),

  // BMW-Style Intro Splash Animation
  splashScreen: document.getElementById("splashScreen"),
  btnSkipSplash: document.getElementById("btnSkipSplash"),
  brandBox: document.getElementById("brandBox"),
};

// -------------------------------------------------------------
// Initialization
// -------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  initSplash();
  initClock();
  setupTabs();
  setupEventListeners();
  if (window.CinematicLotController) {
    window.CinematicLotController.init();
  }
  loadAllData();

  // Auto-refresh stats & slots every 10 seconds
  setInterval(loadAllData, 10000);
});

// -------------------------------------------------------------
// BMW-Style Intro Splash Screen Controller
// -------------------------------------------------------------
function initSplash() {
  const splash = DOM.splashScreen;
  if (!splash) return;

  let timer = null;
  let isDismissed = false;

  function dismiss() {
    if (isDismissed) return;
    isDismissed = true;
    if (timer) clearTimeout(timer);

    splash.classList.add("splash-hidden");
    setTimeout(() => {
      splash.style.display = "none";
    }, 700);
  }

  // Auto-transition into dashboard after complete reveal (3.4s)
  timer = setTimeout(dismiss, 3400);

  // Click-to-skip button
  if (DOM.btnSkipSplash) {
    DOM.btnSkipSplash.addEventListener("click", (e) => {
      e.stopPropagation();
      dismiss();
    });
  }

  // Clicking splash screen skips directly
  splash.addEventListener("click", dismiss);

  // Click brand header box to replay splash animation anytime
  if (DOM.brandBox) {
    DOM.brandBox.addEventListener("click", () => {
      isDismissed = false;
      splash.style.display = "flex";
      // Clone/replace node to re-trigger SVG stroke and CSS keyframe animations
      const newSplash = splash.cloneNode(true);
      splash.parentNode.replaceChild(newSplash, splash);
      DOM.splashScreen = newSplash;
      DOM.btnSkipSplash = document.getElementById("btnSkipSplash");
      initSplash();
    });
  }
}

function initClock() {
  function update() {
    const now = new Date();
    DOM.liveClock.textContent = now.toLocaleTimeString("en-US", { hour12: false });
  }
  update();
  setInterval(update, 1000);
}

// -------------------------------------------------------------
// Navigation & Workspace Tabs
// -------------------------------------------------------------
function setupTabs() {
  DOM.tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      switchTab(targetId);
    });
  });
}

function switchTab(tabId) {
  DOM.tabButtons.forEach(btn => {
    btn.classList.toggle("active", btn.getAttribute("data-tab") === tabId);
  });
  DOM.tabContents.forEach(content => {
    content.classList.toggle("active", content.id === tabId);
  });
}

// -------------------------------------------------------------
// Data Fetching & Sync
// -------------------------------------------------------------
async function loadAllData() {
  await Promise.all([
    fetchStats(),
    fetchSlots(),
    fetchActiveEntries(),
    fetchHistory(),
  ]);
}

async function fetchStats() {
  try {
    const res = await fetch(`${API_BASE}/api/stats`);
    const data = await res.json();
    if (data.success) {
      state.stats = data.stats;
      renderKPIs(data.stats);
    }
  } catch (err) {
    console.error("Failed to fetch stats:", err);
  }
}

function renderKPIs(stats) {
  DOM.kpiTotal.textContent = stats.total_slots || 20;
  DOM.kpiOccupied.textContent = stats.occupied_slots || 0;
  DOM.kpiVacant.textContent = stats.vacant_slots || 0;
  DOM.kpiRevenue.textContent = `₹${(stats.total_revenue || 0).toFixed(2)}`;

  const nextSlot = stats.next_vacant_slot || "FULL";
  DOM.kpiNextSlot.textContent = nextSlot;
  DOM.entryPreviewSlot.textContent = nextSlot;
}

async function fetchSlots() {
  try {
    const res = await fetch(`${API_BASE}/api/slots`);
    const data = await res.json();
    if (data.success) {
      state.slots = data.slots;
      renderSlotsGrid();
      if (window.CinematicLotController && window.CinematicLotController.syncSlots) {
        window.CinematicLotController.syncSlots(data.slots);
      }
    }
  } catch (err) {
    console.error("Failed to fetch slots:", err);
  }
}

async function fetchActiveEntries() {
  try {
    const res = await fetch(`${API_BASE}/api/active`);
    const data = await res.json();
    if (data.success) {
      state.activeEntries = data.active_entries;
      renderActiveDropdown(data.active_entries);
    }
  } catch (err) {
    console.error("Failed to fetch active entries:", err);
  }
}

function renderActiveDropdown(entries) {
  const currentVal = DOM.selectActiveVehicle.value;
  DOM.selectActiveVehicle.innerHTML = `<option value="">-- Choose active parked car (${entries.length}) --</option>`;
  entries.forEach(e => {
    const opt = document.createElement("option");
    opt.value = e.vehicle_no;
    const durStr = e.duration_str ? ` [${e.duration_str}]` : "";
    const feeStr = e.current_amount !== undefined ? ` • ₹${Number(e.current_amount).toFixed(0)}` : "";
    opt.textContent = `${e.vehicle_no} • Bay ${e.slot_no}${durStr}${feeStr}`;
    DOM.selectActiveVehicle.appendChild(opt);
  });
  if (currentVal) {
    DOM.selectActiveVehicle.value = currentVal;
  }
}

async function fetchHistory() {
  try {
    const res = await fetch(`${API_BASE}/api/history?limit=100`);
    const data = await res.json();
    if (data.success) {
      state.history = data.history;
      renderHistoryTable(data.history);
    }
  } catch (err) {
    console.error("Failed to fetch history:", err);
  }
}

// -------------------------------------------------------------
// Visual 2D Parking Bay Grid
// -------------------------------------------------------------
function renderSlotsGrid() {
  DOM.slotsGrid.innerHTML = "";
  const filter = state.currentFilter;

  const filteredSlots = state.slots.filter(s => {
    if (filter === "vacant") return s.status === "Vacant";
    if (filter === "occupied") return s.status === "Occupied";
    return true;
  });

  if (filteredSlots.length === 0) {
    DOM.slotsGrid.innerHTML = `<div class="text-muted" style="grid-column: 1/-1; text-align: center; padding: 40px;">No bays match the selected filter.</div>`;
    return;
  }

  filteredSlots.forEach(slot => {
    const isOccupied = slot.status === "Occupied";
    const card = document.createElement("div");
    card.className = `bay-card ${isOccupied ? "occupied" : "vacant"}`;
    card.id = `bay-${slot.slot_no}`;

    card.innerHTML = `
      <div class="bay-header">
        <span class="bay-no">${slot.slot_no}</span>
        <span class="bay-status-badge">${slot.status.toUpperCase()}</span>
      </div>

      ${isOccupied ? `
        <div class="plate-pill">
          <span class="plate-ind">IND</span>
          <span>${slot.vehicle_no}</span>
        </div>
      ` : `
        <div class="vacant-silhouette">
          <span>🅿</span>
          <span>AVAILABLE</span>
        </div>
      `}

      <div class="bay-footer">
        <span>${isOccupied ? "Occupied Bay" : "Ready to Allot"}</span>
        <button class="bay-action-btn" type="button">
          ${isOccupied ? "Checkout ➜" : "Allot ➜"}
        </button>
      </div>
    `;

    card.addEventListener("click", () => handleSlotClick(slot));
    DOM.slotsGrid.appendChild(card);
  });
}

function handleSlotClick(slot) {
  if (slot.status === "Occupied") {
    switchTab("tab-exit");
    DOM.inputExitTarget.value = slot.vehicle_no;
    DOM.selectActiveVehicle.value = slot.vehicle_no;
    previewBilling(slot.vehicle_no);
  } else {
    switchTab("tab-entry");
    DOM.inputVehicleNo.focus();
  }
}

// -------------------------------------------------------------
// Vehicle Entry & Duplicate Prevention
// -------------------------------------------------------------
async function handleVehicleEntry(e) {
  e.preventDefault();
  const vehicleNo = DOM.inputVehicleNo.value.trim().toUpperCase();
  DOM.entryErrorAlert.classList.add("hidden");

  if (!vehicleNo) {
    showToast("Please enter a vehicle registration number.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/entry`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vehicle_no: vehicleNo }),
    });

    const data = await res.json();

    if (!data.success) {
      // DUPLICATE REJECTION or FULL
      DOM.entryErrorTitle.textContent = "Entry Denied";
      DOM.entryErrorMessage.textContent = data.message;
      DOM.entryErrorAlert.classList.remove("hidden");
      showToast(data.message, "error");
      return;
    }

    // SUCCESS
    DOM.inputVehicleNo.value = "";
    showToast(`Vehicle ${vehicleNo} allotted bay ${data.details.slot_no}!`, "success");
    if (window.CinematicLotController && window.CinematicLotController.dispatchEntryCar) {
      window.CinematicLotController.dispatchEntryCar(data.details.slot_no, vehicleNo);
    }
    loadAllData();

    // Show Entry Pass Receipt
    showReceiptModal(
      "Park Wave - Entry Pass",
      data.details.receipt,
      data.details.ticket_no
    );
  } catch (err) {
    console.error("Entry error:", err);
    showToast("Server communication failed.", "error");
  }
}

// -------------------------------------------------------------
// Exit & Smart Billing Calculation
// -------------------------------------------------------------
async function previewBilling(identifier) {
  const target = (identifier || DOM.inputExitTarget.value || DOM.selectActiveVehicle.value).trim();
  if (!target) {
    showToast("Please select or enter a vehicle number.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/exit/preview`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: target }),
    });

    const data = await res.json();
    if (!data.success) {
      showToast(data.message, "error");
      resetBillDisplay();
      return;
    }

    const item = data.data;
    const p = item.pricing;

    DOM.billVehicle.textContent = item.vehicle_no;
    DOM.billSlot.textContent = item.slot_no;
    DOM.billEntryTime.textContent = item.entry_time;
    DOM.billExitTime.textContent = item.preview_time;
    DOM.billDuration.textContent = p.duration_str;
    DOM.billBilledHours.textContent = `${p.billed_hours} hr(s) (1 base + ${p.additional_hours} addl)`;
    DOM.billHourlyCharge.textContent = `₹${p.hourly_charge.toFixed(2)} (${p.additional_hours} × ₹20)`;
    DOM.billTotalAmount.textContent = `₹${p.total_amount.toFixed(2)}`;
    DOM.billStatus.textContent = "Tariff Computed";

    DOM.btnConfirmExit.disabled = false;
    state.currentExitTarget = item.vehicle_no;
  } catch (err) {
    console.error("Preview bill error:", err);
    showToast("Failed to calculate billing.", "error");
  }
}

function resetBillDisplay() {
  DOM.billVehicle.textContent = "---";
  DOM.billSlot.textContent = "---";
  DOM.billEntryTime.textContent = "---";
  DOM.billExitTime.textContent = "---";
  DOM.billDuration.textContent = "---";
  DOM.billBilledHours.textContent = "---";
  DOM.billHourlyCharge.textContent = "₹0.00";
  DOM.billTotalAmount.textContent = "₹0.00";
  DOM.billStatus.textContent = "Ready";
  DOM.btnConfirmExit.disabled = true;
  state.currentExitTarget = null;
}

async function handleVehicleExit() {
  if (!state.currentExitTarget) return;

  try {
    const res = await fetch(`${API_BASE}/api/exit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ identifier: state.currentExitTarget }),
    });

    const data = await res.json();
    if (!data.success) {
      showToast(data.message, "error");
      return;
    }

    const exitedSlot = data.details.slot_no;
    showToast(`Vehicle ${data.details.vehicle_no} checkout complete!`, "success");
    if (window.CinematicLotController && window.CinematicLotController.dispatchExitCar && exitedSlot) {
      window.CinematicLotController.dispatchExitCar(exitedSlot);
    }
    resetBillDisplay();
    DOM.inputExitTarget.value = "";
    DOM.selectActiveVehicle.value = "";
    loadAllData();

    // Show Final Tax Invoice Receipt
    showReceiptModal(
      "Park Wave - Final Tax Invoice / Receipt",
      data.details.detailed_bill || data.details.receipt,
      data.details.ticket_no
    );
  } catch (err) {
    console.error("Exit execution error:", err);
    showToast("Failed to process vehicle exit.", "error");
  }
}

// -------------------------------------------------------------
// Search Vehicle
// -------------------------------------------------------------
async function handleSearchVehicle() {
  const query = DOM.searchQueryInput.value.trim().toUpperCase();
  DOM.searchResultContainer.classList.add("hidden");
  DOM.searchNotFoundAlert.classList.add("hidden");

  if (!query) {
    showToast("Please enter a vehicle registration number.", "error");
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
    const data = await res.json();

    if (!data.success) {
      DOM.searchNotFoundAlert.classList.remove("hidden");
      return;
    }

    const rec = data.data;
    DOM.searchResultSlot.textContent = rec.slot_no;
    DOM.searchResultPlate.textContent = rec.vehicle_no;
    DOM.searchResultTicket.textContent = `#${rec.ticket_no}`;
    DOM.searchResultEntry.textContent = rec.entry_time;
    DOM.searchResultDuration.textContent = rec.current_duration || "Just entered";
    DOM.searchResultAmount.textContent = `₹${(rec.estimated_amount || 50).toFixed(2)}`;

    DOM.searchResultContainer.classList.remove("hidden");
    state.searchedSlot = rec.slot_no;
  } catch (err) {
    console.error("Search error:", err);
    showToast("Search failed.", "error");
  }
}

function handleGoToSlot() {
  if (!state.searchedSlot) return;
  switchTab("tab-grid");
  const el = document.getElementById(`bay-${state.searchedSlot}`);
  if (el) {
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    el.style.boxShadow = "0 0 30px #38bdf8";
    setTimeout(() => {
      el.style.boxShadow = "";
    }, 2500);
  }
}

// -------------------------------------------------------------
// Activity Ledger Table & CSV Export
// -------------------------------------------------------------
function renderHistoryTable(records) {
  const filter = (DOM.ledgerFilterInput.value || "").trim().toUpperCase();
  DOM.historyTableBody.innerHTML = "";

  const filtered = records.filter(r => {
    if (!filter) return true;
    return (
      r.vehicle_no.toUpperCase().includes(filter) ||
      r.slot_no.toUpperCase().includes(filter) ||
      String(r.ticket_no).includes(filter)
    );
  });

  if (filtered.length === 0) {
    DOM.historyTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 30px;">No entries found.</td></tr>`;
    return;
  }

  filtered.forEach(r => {
    const isCompleted = Boolean(r.exit_time);
    const tr = document.createElement("tr");

    tr.innerHTML = `
      <td><strong>#${r.ticket_no}</strong></td>
      <td><span class="plate-badge">${r.vehicle_no}</span></td>
      <td><strong>${r.slot_no}</strong></td>
      <td>${r.entry_time}</td>
      <td>${r.exit_time || "---"}</td>
      <td><strong>${r.amount !== null ? `₹${Number(r.amount).toFixed(2)}` : "Active"}</strong></td>
      <td>
        <span class="badge ${isCompleted ? 'badge-info' : 'badge-success'}">
          ${isCompleted ? 'COMPLETED' : 'ACTIVE'}
        </span>
      </td>
    `;
    DOM.historyTableBody.appendChild(tr);
  });
}

function exportLedgerToCsv() {
  if (!state.history || state.history.length === 0) {
    showToast("No records to export.", "info");
    return;
  }

  const headers = ["Ticket No", "Vehicle No", "Slot No", "Entry Time", "Exit Time", "Amount", "Status"];
  const rows = state.history.map(r => [
    r.ticket_no,
    r.vehicle_no,
    r.slot_no,
    `"${r.entry_time}"`,
    r.exit_time ? `"${r.exit_time}"` : '""',
    r.amount !== null ? r.amount : '""',
    r.exit_time ? "COMPLETED" : "ACTIVE",
  ]);

  const csvContent = [headers.join(","), ...rows.map(e => e.join(","))].join("\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `park_wave_ledger_${new Date().toISOString().slice(0, 10)}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast("Ledger exported to CSV!", "success");
}

// -------------------------------------------------------------
// Official Receipt Modal Dialog
// -------------------------------------------------------------
function showReceiptModal(title, receiptText, ticketNo) {
  state.currentReceipt = { text: receiptText, ticketNo };
  DOM.receiptDialogTitle.textContent = title;
  DOM.receiptContent.textContent = receiptText;
  // Generate a pseudo barcode visual
  if (DOM.receiptBarcode) {
    const bars = Array.from({ length: 48 }, () => (Math.random() > 0.5 ? "|": " ")).join("");
    DOM.receiptBarcode.textContent = bars;
  }
  DOM.receiptDialog.showModal();
}

function downloadReceiptFile() {
  const text = state.currentReceipt.text;
  const ticketNo = state.currentReceipt.ticketNo || 1;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `park_wave_receipt_ticket_${ticketNo}.txt`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
  showToast("Receipt downloaded as text file.", "success");
}

// -------------------------------------------------------------
// Clear All Data
// -------------------------------------------------------------
async function handleClearData() {
  const ans = confirm("Clear ALL parking records and reset all 20 bays to Vacant?\n\nThis will permanently remove all active and historical entries.");
  if (!ans) return;

  try {
    const res = await fetch(`${API_BASE}/api/clear_data`, { method: "POST" });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, "success");
      if (window.CinematicLotController && window.CinematicLotController.clearAll) {
        window.CinematicLotController.clearAll();
      }
      loadAllData();
    } else {
      showToast(data.message, "error");
    }
  } catch (err) {
    console.error("Clear error:", err);
    showToast("Failed to clear database.", "error");
  }
}

// -------------------------------------------------------------
// Toast Notifications
// -------------------------------------------------------------
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  const icon = type === "success" ? "✔" : type === "error" ? "⚠️" : "ℹ️";
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  DOM.toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// -------------------------------------------------------------
// Setup Event Listeners
// -------------------------------------------------------------
function setupEventListeners() {
  // Grid filters
  DOM.filterButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      DOM.filterButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.currentFilter = btn.getAttribute("data-filter");
      renderSlotsGrid();
    });
  });

  DOM.btnRefreshGrid.addEventListener("click", loadAllData);
  DOM.btnClearData.addEventListener("click", handleClearData);

  // Entry form
  DOM.formEntry.addEventListener("submit", handleVehicleEntry);

  // Exit preview and execution
  DOM.selectActiveVehicle.addEventListener("change", e => {
    if (e.target.value) {
      DOM.inputExitTarget.value = e.target.value;
      previewBilling(e.target.value);
    }
  });

  DOM.btnPreviewBill.addEventListener("click", () => previewBilling());
  DOM.inputExitTarget.addEventListener("keypress", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      previewBilling();
    }
  });

  DOM.btnConfirmExit.addEventListener("click", handleVehicleExit);

  // Search
  DOM.btnSearchVehicle.addEventListener("click", handleSearchVehicle);
  DOM.searchQueryInput.addEventListener("keypress", e => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSearchVehicle();
    }
  });
  DOM.btnGoToSlot.addEventListener("click", handleGoToSlot);

  // History
  DOM.ledgerFilterInput.addEventListener("input", () => renderHistoryTable(state.history));
  DOM.btnExportCsv.addEventListener("click", exportLedgerToCsv);
  DOM.btnRefreshHistory.addEventListener("click", fetchHistory);

  // Dialog actions
  DOM.btnDownloadReceipt.addEventListener("click", downloadReceiptFile);
  DOM.btnPrintReceipt.addEventListener("click", () => window.print());
  DOM.btnCloseReceipt.addEventListener("click", () => DOM.receiptDialog.close());
  DOM.btnDismissReceipt.addEventListener("click", () => DOM.receiptDialog.close());

  // Cinema Toggle
  if (DOM.btnToggleCinema) {
    DOM.btnToggleCinema.addEventListener("click", () => {
      if (window.CinematicLotController) {
        window.CinematicLotController.toggleCinema();
      }
    });
  }
}

// =============================================================
// CINEMATIC LOT CONTROLLER
// Real-time aerial parking simulation with SVG cars, physics,
// glowing bay beacons, parallax, and live database synchronization
// =============================================================
window.CinematicLotController = (function () {
  let isActive = true;
  let ambientInterval = null;
  const parkedCars = {}; // slot_no -> { element, isDb, vehicleNo, color }
  const movingCars = new Set();

  const CAR_COLORS = ["white", "black", "red", "silver", "bronze"];

  // 20 Parking Bay Coordinate Map (% relative to stage)
  // Calibrated to align seamlessly with top & bottom rows of aerial lot image
  const BAYS = {
    // Upper row (S-01 to S-10) - Angled ~70 deg, approach from upper lane (Westbound / left)
    "S-01": { left: 9, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-02": { left: 18, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-03": { left: 27, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-04": { left: 36, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-05": { left: 45, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-06": { left: 54, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-07": { left: 63, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-08": { left: 72, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-09": { left: 81, top: 14, angle: 70, laneY: 38, laneDir: "west" },
    "S-10": { left: 90, top: 14, angle: 70, laneY: 38, laneDir: "west" },

    // Lower row (S-11 to S-20) - Angled ~70 deg, approach from lower lane (Eastbound / right)
    "S-11": { left: 9.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-12": { left: 18.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-13": { left: 27.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-14": { left: 36.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-15": { left: 45.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-16": { left: 54.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-17": { left: 63.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-18": { left: 72.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-19": { left: 81.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
    "S-20": { left: 90.5, top: 72, angle: 70, laneY: 58, laneDir: "east" },
  };

  function init() {
    buildBeacons();
    setupParallax();
    startTrafficFlow();
  }

  function buildBeacons() {
    if (!DOM.cinemaLotBeacons) return;
    DOM.cinemaLotBeacons.innerHTML = "";

    Object.keys(BAYS).forEach((slotNo) => {
      const bay = BAYS[slotNo];
      const beacon = document.createElement("div");
      beacon.className = "slot-beacon vacant";
      beacon.id = `beacon-${slotNo}`;
      beacon.style.left = `${bay.left}%`;
      beacon.style.top = `${bay.top}%`;
      beacon.style.transform = `translate(-50%, -50%) rotate(${bay.angle}deg)`;

      beacon.innerHTML = `
        <span class="beacon-tag">${slotNo}</span>
        <span class="beacon-dot"></span>
      `;
      DOM.cinemaLotBeacons.appendChild(beacon);
    });
  }

  function updateBeaconState(slotNo, isOccupied) {
    const beacon = document.getElementById(`beacon-${slotNo}`);
    if (!beacon) return;
    beacon.classList.toggle("occupied", isOccupied);
    beacon.classList.toggle("vacant", !isOccupied);
  }

  function createCarNode(color = "white", plate = null) {
    const car = document.createElement("div");
    car.className = `cinema-car car-${color}`;
    car.innerHTML = `
      <div class="car-headlight top"></div>
      <div class="car-headlight bottom"></div>
      <div class="car-light-cone"></div>
      <div class="car-taillight top"></div>
      <div class="car-taillight bottom"></div>
      <div class="car-reverse-beam"></div>
      <div class="car-indicator front-left"></div>
      <div class="car-indicator front-right"></div>
      <div class="car-body">
        <div class="car-hood"></div>
        <div class="car-trunk"></div>
        <div class="car-windshield">
          <div class="car-sunroof"></div>
        </div>
        <div class="car-mirror top"></div>
        <div class="car-mirror bottom"></div>
      </div>
      ${plate ? `<div class="car-plate-tag">${plate}</div>` : ""}
    `;
    return car;
  }

  function setupParallax() {
    if (!DOM.cinemaParallax) return;
    let targetX = 0, targetY = 0;
    let currentX = 0, currentY = 0;

    window.addEventListener("mousemove", (e) => {
      if (!isActive) return;
      const nx = (e.clientX / window.innerWidth - 0.5) * 2;
      const ny = (e.clientY / window.innerHeight - 0.5) * 2;
      targetX = nx * -15;
      targetY = ny * -12;
    });

    function loop() {
      currentX += (targetX - currentX) * 0.08;
      currentY += (targetY - currentY) * 0.08;
      DOM.cinemaParallax.style.transform = `translate3d(${currentX.toFixed(2)}px, ${currentY.toFixed(2)}px, 0) scale(1.03)`;
      requestAnimationFrame(loop);
    }
    requestAnimationFrame(loop);
  }

  // Animate Car Entering and Parking into a specific bay
  function animateCarParking(car, bay, slotNo, onComplete) {
    DOM.cinemaCarsStage.appendChild(car);
    movingCars.add(car);

    const isWest = bay.laneDir === "west";
    const startX = isWest ? 105 : -10; // % across stage
    const laneY = bay.laneY;
    const initialHeading = isWest ? 180 : 0; // degrees

    // 1. Enter lane at approach speed
    car.style.transition = "none";
    car.style.left = `${startX}%`;
    car.style.top = `${laneY}%`;
    car.style.transform = `translate(-50%, -50%) rotate(${initialHeading}deg)`;
    car.style.opacity = "1";

    // Trigger transition along lane toward bay X
    requestAnimationFrame(() => {
      // Travel duration proportional to distance
      const distance = Math.abs(startX - bay.left);
      const laneDuration = Math.max(1.8, distance * 0.035);

      car.style.transition = `left ${laneDuration}s cubic-bezier(0.25, 1, 0.5, 1)`;
      car.style.left = `${bay.left}%`;

      // Ahead of arrival, signal turn and brake
      setTimeout(() => {
        car.classList.add("is-braking");
        if (isWest) {
          car.classList.add("indicating-right");
        } else {
          car.classList.add("indicating-right");
        }
      }, Math.max(200, (laneDuration - 1.0) * 1000));

      // 2. Turn into parking bay
      setTimeout(() => {
        car.classList.remove("is-braking");
        car.classList.remove("indicating-right", "indicating-left");

        car.style.transition = `left 1.4s cubic-bezier(0.3, 0, 0.2, 1), top 1.4s cubic-bezier(0.3, 0, 0.2, 1), transform 1.4s cubic-bezier(0.3, 0, 0.2, 1)`;
        car.style.left = `${bay.left}%`;
        car.style.top = `${bay.top}%`;
        car.style.transform = `translate(-50%, -50%) rotate(${bay.angle}deg)`;

        // 3. Settled in bay
        setTimeout(() => {
          car.classList.add("is-braking");
          setTimeout(() => car.classList.remove("is-braking"), 600);
          updateBeaconState(slotNo, true);
          movingCars.delete(car);
          if (onComplete) onComplete();
        }, 1450);
      }, laneDuration * 1000);
    });
  }

  // Animate Car Reversing out and Driving Away
  function animateCarExit(car, bay, slotNo, onComplete) {
    movingCars.add(car);
    car.classList.add("is-reversing");

    const isWest = bay.laneDir === "west";
    const exitTargetX = isWest ? -15 : 115; // % across stage

    // 1. Reverse back into the lane
    car.style.transition = `left 1.6s cubic-bezier(0.4, 0, 0.2, 1), top 1.6s cubic-bezier(0.4, 0, 0.2, 1), transform 1.6s cubic-bezier(0.4, 0, 0.2, 1)`;
    car.style.top = `${bay.laneY}%`;
    car.style.left = `${bay.left}%`;

    // Bay beacon flashes back to vacant green as car leaves bay!
    setTimeout(() => {
      updateBeaconState(slotNo, false);
    }, 600);

    // 2. Align nose in lane direction and cancel reverse lights
    setTimeout(() => {
      car.classList.remove("is-reversing");
      const forwardHeading = isWest ? 180 : 0;
      car.style.transition = `transform 0.5s ease-out`;
      car.style.transform = `translate(-50%, -50%) rotate(${forwardHeading}deg)`;

      // 3. Accelerate off-screen along lane
      setTimeout(() => {
        car.style.transition = `left 2.2s cubic-bezier(0.4, 0, 1, 1), opacity 0.5s ease 1.8s`;
        car.style.left = `${exitTargetX}%`;

        setTimeout(() => {
          movingCars.delete(car);
          car.remove();
          if (onComplete) onComplete();
        }, 2300);
      }, 550);
    }, 1650);
  }

  // Animate Drive-through traffic cruising through
  function animateDriveThrough(isWest = true) {
    if (movingCars.size > 2 || !isActive) return;

    const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
    const car = createCarNode(color);
    DOM.cinemaCarsStage.appendChild(car);
    movingCars.add(car);

    const laneY = isWest ? 38 : 58;
    const startX = isWest ? 110 : -10;
    const endX = isWest ? -15 : 115;
    const heading = isWest ? 180 : 0;

    car.style.transition = "none";
    car.style.left = `${startX}%`;
    car.style.top = `${laneY}%`;
    car.style.transform = `translate(-50%, -50%) rotate(${heading}deg)`;
    car.style.opacity = "1";

    requestAnimationFrame(() => {
      const duration = 4.5 + Math.random() * 2;
      car.style.transition = `left ${duration}s linear`;
      car.style.left = `${endX}%`;

      setTimeout(() => {
        movingCars.delete(car);
        car.remove();
      }, duration * 1000 + 100);
    });
  }

  // Dispatch live real database entry
  function dispatchEntryCar(slotNo, vehicleNo) {
    const bay = BAYS[slotNo];
    if (!bay) return;

    // Remove any ambient car currently idling in this slot
    if (parkedCars[slotNo] && !parkedCars[slotNo].isDb) {
      parkedCars[slotNo].element.remove();
      delete parkedCars[slotNo];
    }

    const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
    const car = createCarNode(color, vehicleNo);

    parkedCars[slotNo] = { element: car, isDb: true, vehicleNo, color };
    animateCarParking(car, bay, slotNo, () => {
      updateBeaconState(slotNo, true);
    });
  }

  // Dispatch live real database exit
  function dispatchExitCar(slotNo) {
    const bay = BAYS[slotNo];
    const parked = parkedCars[slotNo];

    if (parked && parked.element) {
      delete parkedCars[slotNo];
      animateCarExit(parked.element, bay, slotNo, () => {
        updateBeaconState(slotNo, false);
      });
    } else {
      // If car was not on stage yet, spawn and immediately exit
      if (bay) {
        const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
        const car = createCarNode(color);
        car.style.left = `${bay.left}%`;
        car.style.top = `${bay.top}%`;
        car.style.transform = `translate(-50%, -50%) rotate(${bay.angle}deg)`;
        DOM.cinemaCarsStage.appendChild(car);
        animateCarExit(car, bay, slotNo, () => {
          updateBeaconState(slotNo, false);
        });
      }
    }
  }

  // Sync with DB state on poll/load
  function syncSlots(slots) {
    if (!slots || slots.length === 0) return;

    slots.forEach((s) => {
      const isOccupied = s.status === "Occupied";
      const bay = BAYS[s.slot_no];
      if (!bay) return;

      updateBeaconState(s.slot_no, isOccupied);

      if (isOccupied) {
        if (!parkedCars[s.slot_no]) {
          const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
          const car = createCarNode(color, s.vehicle_no);
          car.style.left = `${bay.left}%`;
          car.style.top = `${bay.top}%`;
          car.style.transform = `translate(-50%, -50%) rotate(${bay.angle}deg)`;
          DOM.cinemaCarsStage.appendChild(car);
          parkedCars[s.slot_no] = { element: car, isDb: true, vehicleNo: s.vehicle_no, color };
        }
      } else {
        if (parkedCars[s.slot_no] && parkedCars[s.slot_no].isDb) {
          parkedCars[s.slot_no].element.remove();
          delete parkedCars[s.slot_no];
        }
      }
    });
  }

  function clearAll() {
    Object.keys(parkedCars).forEach((k) => {
      parkedCars[k].element.remove();
      delete parkedCars[k];
    });
    movingCars.forEach((c) => {
      c.remove();
    });
    movingCars.clear();
    Object.keys(BAYS).forEach((k) => updateBeaconState(k, false));
  }

  // Continuous Staggered Traffic Engine (Every 3.5 to 5.0 seconds)
  function startTrafficFlow() {
    if (ambientInterval) clearInterval(ambientInterval);

    ambientInterval = setInterval(() => {
      if (!isActive) return;
      if (movingCars.size >= 2) return; // Keep it staggered, never crowded

      const roll = Math.random();

      // 45% chance: drive-through traffic in upper or lower lane
      if (roll < 0.45) {
        animateDriveThrough(Math.random() > 0.5);
      }
      // 35% chance: ambient car parks into an open slot (if not DB-occupied)
      else if (roll < 0.8) {
        const vacantBays = Object.keys(BAYS).filter((k) => !parkedCars[k]);
        if (vacantBays.length > 3) { // Leave room for user
          const chosenSlot = vacantBays[Math.floor(Math.random() * vacantBays.length)];
          const bay = BAYS[chosenSlot];
          const color = CAR_COLORS[Math.floor(Math.random() * CAR_COLORS.length)];
          const car = createCarNode(color);
          parkedCars[chosenSlot] = { element: car, isDb: false, color };

          animateCarParking(car, bay, chosenSlot, () => {
            updateBeaconState(chosenSlot, true);
          });
        }
      }
      // 20% chance: ambient parked car exits and departs
      else {
        const ambientParked = Object.keys(parkedCars).filter((k) => !parkedCars[k].isDb);
        if (ambientParked.length > 0) {
          const exitSlot = ambientParked[Math.floor(Math.random() * ambientParked.length)];
          const bay = BAYS[exitSlot];
          const parked = parkedCars[exitSlot];
          delete parkedCars[exitSlot];

          animateCarExit(parked.element, bay, exitSlot, () => {
            updateBeaconState(exitSlot, false);
          });
        }
      }
    }, 4200);
  }

  function toggleCinema() {
    isActive = !isActive;
    if (DOM.cinemaLotBg) {
      DOM.cinemaLotBg.classList.toggle("cinema-hidden", !isActive);
    }
    if (DOM.btnToggleCinema) {
      DOM.btnToggleCinema.classList.toggle("is-inactive", !isActive);
    }
    if (DOM.cinemaToggleText) {
      DOM.cinemaToggleText.textContent = isActive ? "Aerial Lot: Active" : "Aerial Lot: Paused";
    }
    showToast(isActive ? "Aerial Lot Animation Activated" : "Aerial Lot Animation Paused", "info");
  }

  return {
    init,
    syncSlots,
    dispatchEntryCar,
    dispatchExitCar,
    clearAll,
    toggleCinema,
  };
})();

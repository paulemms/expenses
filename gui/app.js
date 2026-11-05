/* Settler GUI — browser UI for the existing settle_expenses.py.
 * Pyodide executes the unchanged Python core; all expense data remains in this tab.
 */
"use strict";

const PYTHON_SOURCE_URL = "../settle_expenses.py";
const PYODIDE_VERSION = "0.27.7";
const expenses = [];
let pyodide = null;
let pythonReady = false;
let nextId = 1;

const $ = (id) => document.getElementById(id);
const form = $("expense-form");
const expenseList = $("expense-list");
const statusEl = $("status");
const methodEl = $("method");

function pounds(cents) {
  return (cents / 100).toLocaleString("en-GB", {
    style: "currency", currency: "GBP", minimumFractionDigits: 2
  });
}
function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[c]));
}
function parseNames(value) {
  return value.split(/[;,]/).map((s) => s.trim()).filter(Boolean);
}
function setStatus(message, kind = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${kind}`.trim();
}

async function initialisePython() {
  try {
    setStatus("Loading Python runtime…");
    pyodide = await loadPyodide({ indexURL: `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/` });
    setStatus("Loading your settlement algorithm…");
    const response = await fetch(PYTHON_SOURCE_URL);
    if (!response.ok) {
      throw new Error(`Could not fetch ${PYTHON_SOURCE_URL} (${response.status}).`);
    }
    const source = await response.text();
    pyodide.FS.writeFile("/settle_expenses.py", source);
    pyodide.runPython("import sys; sys.path.insert(0, '/')");
    pyodide.runPython("import settle_expenses");
    pythonReady = true;
    setStatus("Python ready · your settlement engine is loaded.", "ready");
    render();
  } catch (error) {
    console.error(error);
    setStatus(`Python could not start: ${error.message} Check that you are serving gui/ over HTTP and that settle_expenses.py is in the repository root.`, "error");
  }
}

function expenseForPython() {
  return expenses.map(({ payer, amount, participants }) => ({ payer, amount, participants }));
}
function calculate() {
  if (!pythonReady) return null;
  const pyExpenses = pyodide.toPy(expenseForPython());
  const globals = pyodide.toPy({});
  globals.set("expenses_arg", pyExpenses);
  try {
    const method = methodEl.value;
    const result = pyodide.runPython(
      `settle_expenses.settle_expenses(expenses_arg, method=${JSON.stringify(method)})`,
      { globals }
    );
    const payments = result.toJs({ dict_converter: Object.fromEntries });
    const balancesObj = pyodide.runPython(
      "settle_expenses.net_balances(expenses_arg)",
      { globals }
    );
    const balances = balancesObj.toJs({ dict_converter: Object.fromEntries });
    result.destroy();
    balancesObj.destroy();
    globals.destroy();
    pyExpenses.destroy();
    return { payments, balances };
  } catch (error) {
    globals.destroy();
    pyExpenses.destroy();
    throw error;
  }
}

function renderExpenses() {
  $("expense-count").textContent = expenses.length;
  $("clear-btn").disabled = expenses.length === 0;
  $("export-btn").disabled = expenses.length === 0;
  const total = expenses.reduce((sum, e) => sum + e.amount, 0);
  $("total-expenses").textContent = pounds(total);

  if (!expenses.length) {
    expenseList.innerHTML = `<div class="empty-state">
      <div class="empty-icon">£</div><strong>No expenses yet</strong>
      <span>Add your first shared expense above.</span></div>`;
    return;
  }
  expenseList.innerHTML = expenses.map((e) => `
    <div class="expense-row">
      <div class="expense-symbol">£</div>
      <div class="expense-detail">
        <div class="expense-title">${escapeHtml(e.description || "Shared expense")}</div>
        <div class="expense-meta">Paid by ${escapeHtml(e.payer)} · ${escapeHtml(e.participants.join(", "))}</div>
      </div>
      <div class="expense-amount">${pounds(e.amount)}</div>
      <button class="remove-expense" data-remove="${e.id}" title="Remove expense" aria-label="Remove expense">×</button>
    </div>`).join("");
}

function renderResults() {
  $("balances").innerHTML = "";
  $("payments").innerHTML = "";
  $("result-summary").hidden = true;

  if (!expenses.length) {
    $("payments").innerHTML = `<div class="empty-state compact"><strong>Waiting for expenses</strong>
      <span>Your settlement will appear here.</span></div>`;
    return;
  }
  if (!pythonReady) {
    $("payments").innerHTML = `<div class="empty-state compact"><strong>Python is starting</strong>
      <span>Settlement will be calculated when ready.</span></div>`;
    return;
  }

  try {
    const { payments, balances } = calculate();
    const balanceEntries = [...balances.entries()].filter(([, amount]) => amount !== 0);
    $("balances").innerHTML = balanceEntries.length
      ? balanceEntries.map(([name, amount]) => `<span class="balance-chip ${amount > 0 ? "credit" : "debt"}">
          ${escapeHtml(name)}: ${amount > 0 ? "+" : "−"}${pounds(Math.abs(amount))}</span>`).join("")
      : `<span class="balance-chip credit">Everyone is settled</span>`;

    if (!payments.length) {
      $("payments").innerHTML = `<div class="empty-state compact"><strong>No payments needed</strong>
        <span>Everyone's balances are already settled.</span></div>`;
    } else {
      $("payments").innerHTML = payments.map((p) => `<div class="payment-row">
        <span class="payment-person">${escapeHtml(p.from)}</span>
        <span class="payment-arrow">→</span>
        <span class="payment-person">${escapeHtml(p.to)}</span>
        <span class="payment-amount">${pounds(p.amount)}</span>
      </div>`).join("");
    }
    const method = methodEl.value;
    const nonZero = balanceEntries.length;
    const actual = method === "auto" ? (nonZero <= 18 ? "exact" : "heuristic") : method;
    $("result-summary").innerHTML = `<strong>${payments.length} ${payments.length === 1 ? "payment" : "payments"}</strong>
      to settle ${nonZero} non-zero ${nonZero === 1 ? "balance" : "balances"} · ${actual} method`;
    $("result-summary").hidden = false;
  } catch (error) {
    console.error(error);
    setStatus(`Calculation error: ${error.message}`, "error");
    $("payments").innerHTML = `<div class="empty-state compact"><strong>Could not calculate settlement</strong>
      <span>${escapeHtml(error.message)}</span></div>`;
  }
}
function render() {
  renderExpenses();
  renderResults();
  refreshPeopleList();
}

function refreshPeopleList() {
  const names = new Set();
  for (const e of expenses) {
    names.add(e.payer);
    e.participants.forEach((p) => names.add(p));
  }
  $("people-list").innerHTML = [...names].sort((a, b) => a.localeCompare(b))
    .map((name) => `<option value="${escapeHtml(name)}"></option>`).join("");
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const payer = $("payer").value.trim();
  const participants = parseNames($("participants").value);
  const rawAmount = $("amount").value;
  const amountNumber = Number(rawAmount);
  if (!payer) return setStatus("Enter the payer's name.", "error");
  if (!participants.length) return setStatus("Enter at least one participant.", "error");
  if (new Set(participants).size !== participants.length) return setStatus("A participant appears more than once.", "error");
  if (!Number.isFinite(amountNumber) || amountNumber < 0 || !/^\d+(\.\d{1,2})?$/.test(rawAmount.trim())) {
    return setStatus("Enter a non-negative amount with at most two decimal places.", "error");
  }
  const amount = Math.round(amountNumber * 100);
  expenses.push({
    id: nextId++, description: $("description").value.trim(),
    payer, amount, participants
  });
  form.reset();
  setStatus(pythonReady ? "Expense added · settlement updated." : "Expense added · waiting for Python runtime.", pythonReady ? "ready" : "");
  render();
  $("amount").focus();
});

expenseList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-remove]");
  if (!button) return;
  const id = Number(button.dataset.remove);
  const index = expenses.findIndex((e) => e.id === id);
  if (index >= 0) expenses.splice(index, 1);
  setStatus("Expense removed · settlement updated.", "ready");
  render();
});
$("clear-btn").addEventListener("click", () => {
  if (!expenses.length || !confirm("Remove all expenses?")) return;
  expenses.length = 0;
  setStatus("All expenses cleared.", "ready");
  render();
});
methodEl.addEventListener("change", renderResults);

// CSV export uses the exact column names and integer-pence amounts expected by
// run_csv_tests.py. Description is deliberately not included: core CSV schema
// has only case_id,payer,amount,participants.
$("export-btn").addEventListener("click", () => {
  const header = ["case_id", "payer", "amount", "participants"];
  const rows = expenses.map((e, i) => [1, e.payer, e.amount, e.participants.join(";")]);
  const csv = [header, ...rows].map((row) => row.map(csvEscape).join(",")).join("\r\n");
  downloadBlob(csv, "expenses.csv", "text/csv;charset=utf-8");
});
function csvEscape(value) {
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}
function downloadBlob(content, filename, type) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// Import CSV: small RFC4180-style parser for quoted fields and embedded commas.
// Expected columns: case_id,payer,amount,participants. Amount is integer pence.
function parseCsv(text) {
  const rows = [];
  let row = [], field = "", quoted = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
      else if (c === '"') quoted = false;
      else field += c;
    } else if (c === '"' && field === "") quoted = true;
    else if (c === ",") { row.push(field); field = ""; }
    else if (c === "\n") { row.push(field.replace(/\r$/, "")); rows.push(row); row = []; field = ""; }
    else field += c;
  }
  if (field.length || row.length) { row.push(field.replace(/\r$/, "")); rows.push(row); }
  return rows.filter((r) => r.some((v) => v.trim() !== ""));
}
$("import-btn").addEventListener("click", () => $("csv-file").click());
$("csv-file").addEventListener("change", async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  try {
    const rows = parseCsv(await file.text());
    if (rows.length < 2) throw new Error("CSV contains no expense rows.");
    const headers = rows[0].map((h) => h.trim());
    const required = ["case_id", "payer", "amount", "participants"];
    const indexes = Object.fromEntries(required.map((h) => [h, headers.indexOf(h)]));
    const missing = required.filter((h) => indexes[h] < 0);
    if (missing.length) throw new Error(`Missing CSV column(s): ${missing.join(", ")}`);

    const caseIndex = headers.indexOf("case_id");
    const caseIds = new Set(rows.slice(1).map((row) => (row[caseIndex] || "").trim()));
    if (caseIds.size > 1) {
      throw new Error("This GUI represents one settlement scenario at a time. Import a CSV containing only one case_id.");
    }

    const imported = [];
    for (let i = 1; i < rows.length; i++) {
      const row = rows[i];
      if (row.length !== headers.length) throw new Error(`Malformed CSV row ${i + 1}.`);
      const raw = row[indexes.amount].trim();
      if (!/^\d+$/.test(raw)) throw new Error(`Row ${i + 1}: amount must be integer pence.`);
      const payer = row[indexes.payer].trim();
      const participants = parseNames(row[indexes.participants]);
      if (!payer || !participants.length) throw new Error(`Row ${i + 1}: payer and participants are required.`);
      if (new Set(participants).size !== participants.length) throw new Error(`Row ${i + 1}: duplicate participant.`);
      imported.push({ id: nextId++, description: "", payer, amount: Number(raw), participants });
    }
    expenses.push(...imported);
    setStatus(`Imported ${imported.length} expense(s).`, "ready");
    render();
  } catch (error) {
    setStatus(`Import failed: ${error.message}`, "error");
  } finally {
    event.target.value = "";
  }
});

initialisePython();

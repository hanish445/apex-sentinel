import hashlib
import json
import os
from datetime import datetime
from fpdf import FPDF

LEDGER_PATH = os.path.join('reports', 'secure_ledger.json')
PDF_DIR = os.path.join('reports', 'evidence')

def get_previous_hash(ledger_data):
    if not ledger_data:
        return "0000000000000000000000000000000000000000000000000000000000000000"
    return ledger_data[-1]['integrity_hash']

def generate_chained_hash(event_data, previous_hash):
    payload = json.dumps(event_data, sort_keys=True) + previous_hash
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def log_to_ledger(event_report):
    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)

    ledger_data = []
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, 'r') as f:
                ledger_data = json.load(f)
        except json.JSONDecodeError:
            ledger_data = []

    previous_hash = get_previous_hash(ledger_data)

    verification_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "classification": event_report.get("classification"),
        "severity": event_report.get("severity"),
        "top_features": event_report.get("top_features")
    }

    current_hash = generate_chained_hash(verification_data, previous_hash)

    entry = {
        "id": f"EVT-{len(ledger_data) + 1:04d}",
        "timestamp": verification_data['timestamp'],
        "previous_hash": previous_hash,
        "integrity_hash": current_hash,
        "data": event_report
    }

    ledger_data.append(entry)
    with open(LEDGER_PATH, 'w') as f:
        json.dump(ledger_data, f, indent=4)

    pdf_path = generate_forensic_pdf(entry)

    return entry["id"], entry["integrity_hash"], pdf_path

def generate_forensic_pdf(entry):
    pdf = FPDF()
    pdf.add_page()

    # -- Header --
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "APEX SENTINEL // FORENSIC INCIDENT REPORT", ln=True, align='C')
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Automated Cyber-Physical Security Engine v2.5.0", ln=True, align='C')
    pdf.line(10, 30, 200, 30)

    # -- Incident Details --
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "EVENT ID:", 0)
    pdf.set_font("Courier", '', 12)
    pdf.cell(0, 10, entry['id'], ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "TIMESTAMP:", 0)
    pdf.set_font("Courier", '', 12)
    pdf.cell(0, 10, entry['timestamp'], ln=True)

    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "TYPE:", 0)
    pdf.set_font("Courier", 'B', 12)
    pdf.cell(0, 10, entry['data']['classification'], ln=True)

    pdf.ln(10)

    # -- Technical Data --
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "ROOT CAUSE ANALYSIS:", ln=True)
    pdf.set_font("Courier", '', 10)

    for feat, score in entry['data']['top_features']:
        raw_val = entry['data']['raw_snapshot'].get(feat, "N/A")
        pdf.cell(0, 8, f" - {feat}: Deviation {score:.4f} (Sensor Value: {raw_val})", ln=True)

    # -- Chain of Custody --
    pdf.ln(30)
    pdf.set_fill_color(240, 240, 240)
    pdf.rect(10, pdf.get_y(), 190, 40, 'F')

    pdf.set_xy(15, pdf.get_y() + 5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, "CRYPTOGRAPHIC CHAIN OF CUSTODY", ln=True)

    pdf.set_font("Arial", '', 8)
    pdf.cell(0, 5, "This document is digitally linked to the secure ledger. Any modification renders the chain invalid.", ln=True)

    pdf.ln(5)
    pdf.set_font("Courier", 'B', 9)
    pdf.cell(35, 5, "PREVIOUS HASH:", 0)
    pdf.cell(0, 5, entry['previous_hash'], ln=True)

    pdf.cell(35, 5, "EVENT HASH:", 0)
    pdf.cell(0, 5, entry['integrity_hash'], ln=True)

    # -- Save --
    filename = f"{entry['id']}_Receipt.pdf"
    full_path = os.path.join(PDF_DIR, filename)
    pdf.output(full_path)

    return filename
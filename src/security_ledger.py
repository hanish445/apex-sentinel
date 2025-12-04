import hashlib
import json
import os
from datetime import datetime
from fpdf import FPDF

# Base path for reports
REPORTS_DIR = 'reports'
LEDGER_FILE = 'secure_ledger.json'

def get_previous_hash(ledger_path):
    """Retrieves the hash of the last entry or returns Genesis hash."""
    if not os.path.exists(ledger_path):
        return "0000000000000000000000000000000000000000000000000000000000000000"

    try:
        with open(ledger_path, 'r') as f:
            data = json.load(f)
            return data[-1]['integrity_hash'] if data else "0000000000000000000000000000000000000000000000000000000000000000"
    except:
        return "0000000000000000000000000000000000000000000000000000000000000000"

def generate_chained_hash(event_data, previous_hash):
    payload = json.dumps(event_data, sort_keys=True) + previous_hash
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()

def log_to_ledger(event_report, metadata):
    """
    Logs event to chain and generates structured PDF evidence.
    """
    # 1. Setup Organized Paths
    year = str(metadata.get('year', 'Unknown'))
    gp = metadata.get('gp', 'Unknown_GP')
    driver = metadata.get('driver', 'Unknown_Driver')

    # Evidence Folder: reports/evidence/2023/Bahrain/PER/
    evidence_dir = os.path.join(REPORTS_DIR, 'evidence', year, gp, driver)
    os.makedirs(evidence_dir, exist_ok=True)

    ledger_path = os.path.join(REPORTS_DIR, LEDGER_FILE)

    # 2. Blockchain Logic
    previous_hash = get_previous_hash(ledger_path)

    verification_payload = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "type": event_report.get("classification"),
        "top_features": event_report.get("top_features")
    }

    integrity_hash = generate_chained_hash(verification_payload, previous_hash)

    event_id = f"EVT-{datetime.now().strftime('%Y%m%d')}-{integrity_hash[:6].upper()}"

    entry = {
        "id": event_id,
        "timestamp": verification_payload['timestamp'],
        "metadata": metadata,
        "previous_hash": previous_hash,
        "integrity_hash": integrity_hash,
        "data": event_report
    }

    # 3. Save to Ledger
    ledger_data = []
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, 'r') as f:
                ledger_data = json.load(f)
        except: pass

    ledger_data.append(entry)
    with open(ledger_path, 'w') as f:
        json.dump(ledger_data, f, indent=4)

    # 4. Generate Professional PDF
    pdf_filename = f"{event_id}_Evidence.pdf"
    pdf_path = os.path.join(evidence_dir, pdf_filename)
    generate_professional_pdf(entry, pdf_path)

    return event_id, integrity_hash, pdf_filename

def generate_professional_pdf(entry, filepath):
    pdf = FPDF()
    pdf.add_page()

    # -- BRANDING HEADER --
    pdf.set_fill_color(20, 20, 20) # Almost Black
    pdf.rect(0, 0, 210, 40, 'F')

    pdf.set_xy(10, 10)
    pdf.set_font("Arial", 'B', 24)
    pdf.set_text_color(255, 255, 255) # White
    pdf.cell(0, 10, "APEX SENTINEL", ln=True)

    pdf.set_font("Arial", 'I', 10)
    pdf.set_text_color(225, 6, 0) # F1 Red
    pdf.cell(0, 5, "CYBER-PHYSICAL INTEGRITY MONITOR", ln=True)

    # -- TITLE --
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 50)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "EVIDENCE COLLECTED FROM APEX SENTINEL", ln=True, align='C')
    pdf.line(10, 62, 200, 62)

    # -- SESSION CONTEXT --
    meta = entry['metadata']
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(95, 8, f"  GRAND PRIX: {meta.get('year')} {meta.get('gp')}", 0, 0, 'L', 1)
    pdf.cell(95, 8, f"  DRIVER: {meta.get('driver')}", 0, 1, 'L', 1)
    pdf.cell(95, 8, f"  SESSION: {meta.get('session')}", 0, 0, 'L', 1)
    pdf.cell(95, 8, f"  TIMESTAMP: {entry['timestamp']}", 0, 1, 'L', 1)

    # -- INCIDENT DETAILS --
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"DETECTED ANOMALY: {entry['data'].get('classification')}", ln=True)

    pdf.set_font("Arial", '', 11)
    pdf.multi_cell(0, 6, "Apex Sentinel AI detected a deviation from the expected physical baseline. The following sensor telemetry triggered the alert logic.")

    pdf.ln(5)
    pdf.set_font("Courier", 'B', 10)
    for feat, score in entry['data']['top_features']:
        raw = entry['data']['raw_snapshot'].get(feat, "N/A")
        pdf.cell(0, 6, f">> {feat.upper().ljust(10)} | DEVIATION: {score:.4f} | RAW VALUE: {raw}", ln=True)

    # -- SECURITY SEAL --
    pdf.set_y(-60)
    pdf.set_font("Arial", 'B', 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "CRYPTOGRAPHIC CHAIN OF CUSTODY", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())

    pdf.ln(2)
    pdf.set_font("Courier", '', 7)
    pdf.cell(30, 4, "EVENT ID:", 0)
    pdf.cell(0, 4, entry['id'], ln=True)

    pdf.cell(30, 4, "INTEGRITY HASH:", 0)
    pdf.cell(0, 4, entry['integrity_hash'], ln=True)

    pdf.cell(30, 4, "PREV BLOCK:", 0)
    pdf.cell(0, 4, entry['previous_hash'], ln=True)

    pdf.output(filepath)
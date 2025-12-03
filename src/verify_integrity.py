import json
import os
import sys

from security_ledger import generate_chained_hash

LEDGER_PATH = os.path.join('reports', 'secure_ledger.json')

def verify_ledger():
    print("\n Starting forensic integrity scan...")
    print(f"Scanning Ledger: {LEDGER_PATH}")

    if not os.path.exists(LEDGER_PATH):
        print("Error: Ledger file not found")
        return

    try:
        with open(LEDGER_PATH, 'r') as f:
            ledger = json.load(f)
    except Exception as e:
        print(f"Corruption Detected! The file is not valid JSON. {e}")
        return

    is_clean = True
    previous_hash = "0000000000000000000000000000000000000000000000000000000000000000"

    for i, entry in enumerate(ledger):
        print(f"[Block {i+1}] checking ID: {entry['id']}...", end=" ")
        verification_data = {
            "timestamp":entry['timestamp'],
            "classification": entry['data'].get("classification"),
            "severity": entry['data'].get("severity"),
            "top_features": entry['data'].get("top_features")
        }

        if entry['previous_hash'] != previous_hash:
            print("Broken Link!")
            print(f"     Expected Prev: {previous_hash[.16]}...")
            print(f"     Found Prev: {entry['previous_hash'][:16]}")
            is_clean = False
            break

        calculated_hash = generate_chained_hash(verification_data, previous_hash)

        if calculated_hash != entry['integrity_hash']:
            print("Tampering Detected!")
            print(f"     Stored Hash: {entry['integrity_hash'][:16]}...")
            print(f"     Calculated: {calculated_hash[:16]}...")
            print("      >>> Content modification confirmed <<<")
            is_clean = False
            break

        print("Verified!")
        previous_hash = entry['integrity_hash']

    print("-" * 40)
    if is_clean:
        print("SYSTEM INTEGRITY VERIFIED. NO TAMPERING FOUND.")
    else:
        print("CRITICAL SECURITY FAILURE. LEDGER IS COMPROMISED.")

if __name__ == "__main__":
    verify_ledger()
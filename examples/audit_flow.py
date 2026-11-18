"""Full audit flow example for WaveBrute.

Demonstrates the complete ethical auditing pipeline including the new
optional hashcat export for real offline cracking. All steps run in
safe simulation mode.
"""

import os
from wavebrute import Auditor


def main() -> None:
    print("=== WaveBrute Full Ethical Audit Flow ===\n")
    auditor = Auditor(simulation_mode=True, interface="wlan0")

    # 1. Scan
    print("1. Scanning for networks (simulation)...")
    networks = auditor.scan()
    print(f"   Found {len(networks)} networks.\n")

    # 2. Simulate attack
    print("2. Running brute-force simulation on Cafe_Rouge_FreeWiFi...")
    attack = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=6000)
    print(f"   Success: {attack['success']}")
    if attack.get("password"):
        print(f"   Password: {attack['password']}")
    print(f"   Attempts: {attack['attempts']}\n")

    # 3. PMKID simulation
    print("3. Running PMKID simulation on IoT-Devices...")
    pmkid = auditor.simulate_pmkid_attack("IoT-Devices")
    print(f"   Success: {pmkid['success']}")
    print(f"   Notes: {pmkid.get('notes', '')[:80]}...\n")

    # 4. Handshake analysis
    print("4. Analyzing demo handshake capture...")
    analysis = auditor.analyze_handshake("demo.cap")
    print(f"   Crack time estimate: {analysis.get('crack_time_estimate', 'N/A')}")
    print(f"   Has handshake: {analysis.get('has_handshake', False)}\n")

    # 5. Hashcat export for real offline cracking
    print("5. Exporting for hashcat offline cracking...")
    hc_path = auditor.export_for_hashcat(
        ssid="Cafe_Rouge_FreeWiFi",
        output_path="demo_hashcat.22000"
    )
    print(f"   Hashcat file created: {hc_path}")
    print("   (Open the file for hashcat command examples and real-capture guidance)\n")

    # 6. Build report
    print("6. Building professional PDF report...")
    report_path = auditor.build_report(
        title="WaveBrute Full Audit with Hashcat Export",
        output_path="full_audit_report.pdf"
    )
    print(f"   Report saved to: {report_path}\n")

    print("=== Audit flow completed successfully ===")
    print("All operations were performed in safe simulation mode.")
    print("Remember: only use against networks you own or have explicit permission for.")


if __name__ == "__main__":
    main()

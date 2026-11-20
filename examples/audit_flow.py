#!/usr/bin/env python3
"""Full audit flow example demonstrating the complete WaveBrute pipeline.

Includes the new tiny on-device model for password prediction.
All operations run in safe simulation mode.
"""

from wavebrute import Auditor, TinyPasswordModel


def main() -> None:
    print("=== WaveBrute Full Audit Flow Example ===")
    print("All actions are simulated. No real networks are touched.\n")

    auditor = Auditor(simulation_mode=True)

    # 1. Scan (uses AI hints powered by the model)
    print("1. Scanning for networks...")
    networks = auditor.scan()
    print(f"   Found {len(networks)} networks (simulated).")
    for net in networks[:2]:
        print(f"   - {net['ssid']} ({net.get('encryption')})")

    # 2. Demonstrate the tiny on-device model directly
    print("\n2. Training & using tiny on-device password model...")
    model = TinyPasswordModel().train()
    predictions = model.predict("Cafe_Rouge_FreeWiFi", 6)
    print(f"   Top predictions: {predictions}")

    # 3. Targeted wordlist (internally uses the model via generate_ai_suggestions)
    print("\n3. Generating smart wordlist (with model predictions)...")
    wordlist = auditor.wordlist_generator.from_ssid("Cafe_Rouge_FreeWiFi", size=800)
    print(f"   Generated {len(wordlist)} candidates (first 5: {wordlist[:5]})")

    # 4. Simulated attack
    print("\n4. Running brute-force simulation...")
    attack = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=5000)
    print(f"   Success: {attack['success']}")
    if attack.get("password"):
        print(f"   Cracked password: {attack['password']}")

    # 5. PMKID simulation
    print("\n5. Running PMKID simulation...")
    pmkid = auditor.simulate_pmkid_attack("IoT-Devices")
    print(f"   PMKID success: {pmkid['success']}")

    # 6. Direct model prediction via Auditor
    print("\n6. Direct model predictions via Auditor...")
    preds = auditor.predict_passwords("NETGEAR_Guest", num_predictions=5)
    print(f"   Predictions: {preds}")

    # 7. Handshake analysis (simulated)
    print("\n7. Analyzing handshake capture (simulated)...")
    analysis = auditor.analyze_handshake("demo.cap")
    print(f"   Has handshake: {analysis['has_handshake']}")
    print(f"   Crack estimate: {analysis['crack_time_estimate']}")

    # 8. Hashcat export
    print("\n8. Exporting for hashcat...")
    hc_path = auditor.export_for_hashcat("Cafe_Rouge_FreeWiFi")
    print(f"   Hashcat file: {hc_path}")

    # 9. Build PDF report
    print("\n9. Building professional PDF report...")
    report_path = auditor.build_report(title="Example Ethical Audit")
    print(f"   Report saved to: {report_path}")

    print("\n=== Audit flow completed successfully ===")
    print("The tiny on-device model was trained and used throughout.")
    print("All operations respected the Ethics Guard (simulations auto-approved).")


if __name__ == "__main__":
    main()

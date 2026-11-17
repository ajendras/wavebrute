"""Full audit flow example demonstrating the new PMKID simulation module.

Run with: python examples/audit_flow.py
All operations are performed safely in simulation mode.
"""

from wavebrute import Auditor

print("=== WaveBrute Full Ethical Audit Flow (with PMKID) ===")
print("All actions are simulated — no real networks or packets are touched.\n")

auditor = Auditor(simulation_mode=True)

# 1. Scan
networks = auditor.scan()
print(f"Discovered {len(networks)} networks (simulated)")
for net in networks[:2]:  # show first two
    print(f"  • {net['ssid']} ({net['encryption']}, {net['signal']} dBm)")

# 2. Brute-force simulation
attack = auditor.simulate_attack("Cafe_Rouge_FreeWiFi", max_attempts=5000)
print(f"\nBrute-force simulation: {'SUCCESS' if attack['success'] else 'no match'}")
if attack.get("password"):
    print(f"   Password: {attack['password']}")
print(f"   Attempts: {attack['attempts']} in {attack['duration_seconds']}s")

# 3. PMKID simulation (new)
pmkid = auditor.simulate_pmkid_attack("IoT-Devices", max_attempts=4000)
print(f"\nPMKID simulation: {'SUCCESS' if pmkid['success'] else 'no match'}")
if pmkid.get("password"):
    print(f"   Password: {pmkid['password']}")
print(f"   Notes: {pmkid.get('notes', '')[:90]}...")

# 4. Handshake analysis
analysis = auditor.analyze_handshake("demo.cap")
print(f"\nHandshake analysis: {analysis.get('crack_time_estimate', 'N/A')}")

# 5. Generate report
report_path = auditor.build_report(title="PMKID Demo Ethical Audit")
print(f"\nPDF report generated: {report_path}")

print("\n=== Full pipeline with PMKID simulation completed successfully ===")
print("Remember: only use WaveBrute on networks you own or have explicit permission to test.")

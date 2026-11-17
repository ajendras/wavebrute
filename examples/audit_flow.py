"""Runnable end-to-end example of the WaveBrute audit pipeline.

Demonstrates the full recommended flow:
    scan() → WordlistGenerator → simulate_attack() → analyze_handshake() → build_report()

Everything runs in safe simulation mode. No packets are sent, no real networks
are touched. The resulting PDF uses the neo-brutalist visual style (thick
black borders, #ff004d magenta, #00ff9f lime accents).

Run with: python examples/audit_flow.py
"""

import tempfile
from pathlib import Path

from wavebrute.auditor import Auditor
from wavebrute.utils import generate_ai_suggestions
from wavebrute.wordlist import WordlistGenerator


def main() -> None:
    """Execute a complete simulated audit pipeline."""
    print("\n" + "=" * 70)
    print("WAVEBRUTE — FULL ETHICAL AUDIT FLOW EXAMPLE")
    print("=" * 70)
    print("All steps run in SAFE SIMULATION MODE.\n")

    auditor = Auditor(simulation_mode=True, interface="wlan0")

    # 1. Live-like scan (synthetic data)
    print("1. SCANNING NETWORKS")
    print("-" * 40)
    networks = auditor.scan()
    print(f"   → Discovered {len(networks)} networks (simulated)")
    for net in networks[:3]:
        hint = net.get("ai_hint", "")
        print(f"     • {net['ssid']:<22} | {net['encryption']:<8} | {hint}")
    print()

    # 2. Smart wordlist generation
    print("2. GENERATING TARGETED WORDLIST")
    print("-" * 40)
    target_ssid = "Cafe_Rouge_FreeWiFi"
    generator = WordlistGenerator()
    base_list = generator.from_ssid(target_ssid, size=600)

    ai_suggestions = generate_ai_suggestions(target_ssid, max_suggestions=40)
    combined = list(dict.fromkeys(ai_suggestions + base_list))

    print(f"   Base words from SSID : {len(base_list)}")
    print(f"   AI-augmented hints   : {len(ai_suggestions)}")
    print(f"   Final unique list    : {len(combined)} candidates")
    print(f"   Preview: {combined[:6]}")

    # Persist wordlist to temporary file for demo
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as tmp:
        tmp.write("\n".join(combined))
        wordlist_path = tmp.name
    print(f"   Wordlist written to  : {wordlist_path}")
    print()

    # 3. Safe in-memory brute-force simulation
    print("3. SAFE BRUTE-FORCE SIMULATION")
    print("-" * 40)
    attack_result = auditor.simulate_attack(
        ssid=target_ssid,
        wordlist_path=wordlist_path,
        max_attempts=8000,
    )

    print(f"   Success          : {attack_result['success']}")
    if attack_result.get("password"):
        print(f"   Password found   : {attack_result['password']}")
    print(f"   Attempts         : {attack_result['attempts']}")
    print(f"   Duration         : {attack_result['duration_seconds']}s")
    print(f"   AI suggestions used : {attack_result['ai_suggestions_used']}")
    print("   Recommendations:")
    for rec in attack_result["recommendations"]:
        print(f"     • {rec}")
    print()

    # 4. Handshake analysis (simulated)
    print("4. HANDSHAKE ANALYSIS")
    print("-" * 40)
    # Create a dummy capture file so the call doesn't raise
    dummy_cap = Path("demo.cap")
    dummy_cap.write_text("fake handshake data for simulation", encoding="utf-8")

    handshake_info = auditor.analyze_handshake(str(dummy_cap))
    print(f"   Handshake present : {handshake_info['has_handshake']}")
    print(f"   Type              : {handshake_info['handshake_type']}")
    print(f"   Crackable         : {handshake_info['crackable']}")
    print(f"   Estimated time    : {handshake_info['crack_time_estimate']}")
    print("   Note: real cracking would use hashcat/aircrack-ng (authorized only).")
    print()

    # 5. Professional PDF report
    print("5. GENERATING NEO-BRUTALIST PDF REPORT")
    print("-" * 40)
    report_path = auditor.build_report(
        title="WaveBrute Example — Simulated Ethical Audit",
        output_path="example_wavebrute_report.pdf",
    )
    print(f"   Report written to : {report_path}")
    print("   Visual style      : thick 3px borders, hard shadows,")
    print("                       #ff004d magenta + #00ff9f lime accents,")
    print("                       chunky headings, zero rounding.")
    print()

    # Cleanup
    dummy_cap.unlink(missing_ok=True)
    Path(wordlist_path).unlink(missing_ok=True)

    print("=" * 70)
    print("FULL AUDIT FLOW COMPLETED SUCCESSFULLY")
    print("All operations were performed safely in simulation mode.")
    print("Open example_wavebrute_report.pdf to see the loud neo-brutalist output.")
    print("For real engagements: complete the ethics checklist first.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

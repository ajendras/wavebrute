"""Ethics and consent management for responsible auditing.

Prevents accidental or unauthorized use of live scanning or attack features.
Provides an interactive checklist for CLI use and logging of all actions.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


class ConsentManager:
    """Manages user consent and audit logging for ethical compliance.

    All live operations must pass through require_consent(). Simulation
    actions are auto-approved. Checklist is shown for first live action.
    """

    def __init__(self) -> None:
        """Initialize with consent flag off (live actions will prompt)."""
        self.consent_given: bool = False
        self.audit_log: List[Dict[str, Any]] = []
        self.log_file = Path("wavebrute_audit.log")

    def show_checklist(self) -> bool:
        """Display the mandatory ethics checklist and obtain confirmation.

        Returns True only if user explicitly agrees to all points.
        In GUI contexts this would be replaced by a Kivy modal, but here
        it uses CLI for the core library.
        """
        print("\n" + "=" * 60)
        print("WAVEBRUTE ETHICS & LEGAL CONSENT CHECKLIST")
        print("=" * 60)
        print("Before performing any live wireless audit you MUST confirm:")

        checklist = [
            "1. I have explicit written permission from the network owner/operator.",
            "2. This is for authorized security testing or educational demonstration only.",
            "3. I will not use this tool against networks I do not own or have permission for.",
            "4. I understand that capturing handshakes or attempting to crack passwords without authorization may be illegal.",
            "5. I will delete all captured data after the authorized engagement ends.",
            "6. I agree to follow responsible disclosure practices.",
        ]

        for item in checklist:
            print(item)

        print("\nType YES in all caps if you agree to ALL of the above and accept full legal responsibility.")
        try:
            response = input("> ").strip()
            if response == "YES":
                self.consent_given = True
                print("✅ Consent recorded. Proceeding with ethical audit mode.")
                self.log_audit(
                    "consent_granted",
                    {"checklist_completed": True, "timestamp": datetime.now().isoformat()},
                )
                return True
            else:
                print("❌ Consent not given. Live actions blocked.")
                return False
        except KeyboardInterrupt:
            print("\nConsent cancelled.")
            return False
        except Exception:
            print("Error during consent. Live actions blocked.")
            return False

    def require_consent(self, action: str) -> bool:
        """Check or obtain consent for a specific action.

        Simulation actions are always permitted.
        Live actions require prior consent via the checklist.

        Args:
            action: Description of the action (e.g. 'network scan', 'simulated attack on Cafe_Rouge_FreeWiFi')

        Returns:
            bool: True if the action is allowed.

        Raises:
            ValueError: If action is not a valid string.
        """
        if not isinstance(action, str) or not action.strip():
            raise ValueError("action must be a non-empty string describing the intended operation")

        action = action.strip()

        # Auto-approve simulations, analysis, and reporting
        if any(
            keyword in action.lower()
            for keyword in ("simulation", "simulated", "analyze", "handshake analysis", "report", "build_report")
        ):
            return True

        # For live actions, ensure consent
        if not self.consent_given:
            print(f"\n⚠️  Live action requested: {action}")
            print("This requires completing the ethics checklist first.")
            return self.show_checklist()

        return True

    def log_audit(self, action: str, details: Dict[str, Any]) -> None:
        """Record an audit event to in-memory log and optional persistent file.

        Args:
            action: The action performed.
            details: Any contextual data (network count, ssid, success, etc).
        """
        if not isinstance(details, dict):
            details = {"details": str(details)}

        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details,
        }

        self.audit_log.append(entry)

        # Append to log file (best effort - never blocks core functionality)
        try:
            with self.log_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception:
            pass  # non-critical

    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Return copy of the audit trail."""
        return list(self.audit_log)

    def reset_consent(self) -> None:
        """Reset consent state (for testing or new session)."""
        self.consent_given = False


if __name__ == "__main__":
    # Self-contained runnable demo
    cm = ConsentManager()
    print("=== WaveBrute ConsentManager Demo ===")
    print("Simulation action (should auto-approve):")
    print("require_consent('simulated attack on TestNet') ->", cm.require_consent("simulated attack on TestNet"))
    print("\nLive action (will prompt for consent):")
    # Note: interactive in real runs; skipped in automated demo context
    print("Consent checklist can be shown with cm.show_checklist()")
    cm.log_audit("demo_action", {"networks": 4, "simulation": True})
    print(f"Logged {len(cm.get_audit_log())} audit entries.")
    print("Ethics module demo completed.")

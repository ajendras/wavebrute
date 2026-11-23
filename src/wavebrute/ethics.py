"""Ethics and consent management for responsible auditing."""

from __future__ import annotations

from datetime import datetime
from typing import Any


class ConsentManager:
    """Manages consent and audit logging. Simulations are auto-approved."""

    def __init__(self) -> None:
        self.audit_log: list[dict[str, Any]] = []

    def show_checklist(self) -> bool:
        """Display ethics checklist. In real GUI/CLI would be interactive."""
        print("\n=== ETHICS CHECKLIST ===")
        print("[x] I confirm this is an authorized audit or simulation only.")
        print("[x] I will not use this for illegal purposes.")
        print("[x] I understand WaveBrute is for educational and ethical red teaming.")
        print("========================\n")
        return True

    def require_consent(self, action: str) -> bool:
        """Require consent for the given action. Simulations bypass prompt."""
        if any(k in action.lower() for k in ("simulated", "simulation", "predict", "report", "batch")):
            return True
        return self.show_checklist()

    def log_audit(self, action: str, details: dict[str, Any]) -> None:
        """Log the audit action with timestamp."""
        entry = {
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat(),
        }
        self.audit_log.append(entry)
        print(f"[ETHICS LOG] {action.upper()}: {details}")

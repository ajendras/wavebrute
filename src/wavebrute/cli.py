"""CLI entrypoint for WaveBrute.

The ``wavebrute`` command provides five main subcommands that mirror the
core library functionality. Every command defaults to simulation_mode=True
for safety. Use --no-simulation only after completing the ethics checklist.

All commands respect ConsentManager, perform strict validation, and output
loud, clear neo-brutalist-styled text (colours via click.style).

Examples:
    wavebrute scan --simulation
    wavebrute wordlist "MyNetwork" --size 2000 --output custom.txt
    wavebrute attack --ssid "Cafe_Rouge_FreeWiFi"
    wavebrute pmkid --ssid "Vulnerable-Router"
    wavebrute hashcat --ssid "TargetNet"
    wavebrute report --title "My Audit"
"""

import click
from pathlib import Path
from typing import Optional

from .auditor import Auditor
from .wordlist import WordlistGenerator
from .report import ReportBuilder
from .utils import generate_ai_suggestions


@click.group()
@click.version_option(version="0.1.0", prog_name="wavebrute")
def main() -> None:
    """WaveBrute — Ethical WiFi auditing toolkit with neo-brutalist GUI."""


@main.command()
@click.option(
    "--interface",
    "-i",
    default="wlan0",
    help="Wireless interface to use (ignored in simulation mode)",
)
@click.option(
    "--simulation/--no-simulation",
    default=True,
    help="Run in safe in-memory simulation mode (recommended and default)",
)
def scan(interface: str, simulation: bool) -> None:
    """Scan for nearby WiFi networks.

    In simulation mode returns realistic synthetic networks.
    Live mode requires root/monitor mode and explicit consent.
    """
    if not isinstance(interface, str) or not interface.strip():
        raise click.BadParameter("interface must be a non-empty string")

    auditor = Auditor(simulation_mode=simulation, interface=interface)

    click.echo(click.style("\n=== WAVEBRUTE SCANNER ===", fg="magenta", bold=True))
    click.echo(
        click.style(
            f"Mode: {'SIMULATION (safe)' if simulation else 'LIVE (requires consent)'}",
            fg="green" if simulation else "yellow",
        )
    )
    click.echo("-" * 60)

    try:
        networks = auditor.scan(interface)
        click.echo(f"\nDiscovered {len(networks)} network(s):\n")
        for i, net in enumerate(networks, 1):
            ssid = net.get("ssid", "Hidden")
            enc = net.get("encryption", "OPEN")
            sig = net.get("signal", -50)
            bssid = net.get("bssid", "??:??:??:??:??:??")
            ai_hint = net.get("ai_hint", "")
            line = (
                f"{i:2}. {ssid:<24} | {enc:<11} | {sig:4}dBm | {bssid}"
            )
            click.echo(line)
            if ai_hint:
                click.echo(click.style(f"     AI hint: {ai_hint}", fg="bright_green"))
        click.echo("\n" + click.style("Audit logged. Next: wavebrute attack", fg="cyan"))
    except PermissionError as exc:
        click.echo(click.style(f"ETHICS GUARD BLOCKED: {exc}", fg="red", bold=True))
        click.echo("Run 'wavebrute ethics' or complete the checklist first.")
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(click.style(f"Error during scan: {exc}", fg="red"))
        if not simulation:
            click.echo(click.style("Tip: retry with --simulation", fg="yellow"))


@main.command()
@click.argument("ssid", required=True)
@click.option("--size", "-s", default=1500, type=int, help="Approximate wordlist size")
@click.option(
    "--output",
    "-o",
    default="wordlist.txt",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    help="Output file for the generated wordlist",
)
@click.option("--simulation/--no-simulation", default=True)
def wordlist(ssid: str, size: int, output: str, simulation: bool) -> None:
    """Generate a smart targeted wordlist from an SSID.

    Combines SSID-derived candidates, common patterns, and AI suggestions.
    """
    if not ssid or len(ssid.strip()) == 0:
        raise click.BadParameter("ssid cannot be empty")
    if size < 50 or size > 100000:
        raise click.BadParameter("size must be between 50 and 100000")

    click.echo(click.style("\n=== WORDLIST GENERATOR ===", fg="magenta", bold=True))
    click.echo(f"Target SSID : {ssid}")
    click.echo(f"Target size : {size}")

    generator = WordlistGenerator()
    base_words = generator.from_ssid(ssid.strip(), size=size)
    ai_words = generate_ai_suggestions(ssid, max_suggestions=25)
    combined = list(dict.fromkeys(ai_words + base_words))  # preserve order, dedup

    out_path = Path(output)
    out_path.write_text("\n".join(combined), encoding="utf-8")

    click.echo(click.style(f"\nGenerated {len(combined)} candidates", fg="green", bold=True))
    click.echo(f"Saved to    : {out_path.absolute()}")
    click.echo("\nThis list can be used with hashcat/aircrack in authorized engagements only.")


@main.command()
@click.option("--ssid", "-s", required=True, help="Target network SSID")
@click.option(
    "--wordlist",
    "-w",
    type=click.Path(exists=True, dir_okay=False),
    default=None,
    help="Optional path to custom wordlist (uses generated list if omitted)",
)
@click.option("--max-attempts", "-m", default=12000, type=int)
@click.option("--simulation/--no-simulation", default=True, help="Safe simulation only")
def attack(ssid: str, wordlist: Optional[str], max_attempts: int, simulation: bool) -> None:
    """Run a completely safe in-memory brute-force simulation.

    No packets are sent. Demonstrates timing, AI augmentation and cracking logic.
    """
    if not simulation:
        click.echo(click.style("Live attacks are NOT supported.", fg="red", bold=True))
        click.echo("This tool only supports --simulation for ethical reasons.")
        return

    auditor = Auditor(simulation_mode=True)
    click.echo(click.style("\n=== SAFE BRUTE-FORCE SIMULATOR ===", fg="magenta", bold=True))
    click.echo(f"Target SSID : {ssid}")
    click.echo("Mode        : IN-MEMORY SIMULATION (no real traffic)")

    try:
        result = auditor.simulate_attack(
            ssid=ssid,
            wordlist_path=wordlist,
            max_attempts=max_attempts,
        )
        click.echo("\n" + "=" * 50)
        if result.get("success"):
            click.echo(click.style("CRACKED IN SIMULATION!", fg="green", bold=True))
            click.echo(f"Password : {result.get('password')}")
        else:
            click.echo(click.style("No password found in this simulation run.", fg="yellow"))
        click.echo(f"Attempts : {result.get('attempts', 0)}")
        click.echo(f"Duration : {result.get('duration_seconds', 0)}s")
        click.echo(f"AI hints used : {result.get('ai_suggestions_used', 0)}")
        click.echo("\n" + click.style("RECOMMENDATIONS:", fg="cyan", bold=True))
        for rec in result.get("recommendations", []):
            click.echo(f"  • {rec}")
        click.echo("=" * 50)
    except PermissionError as exc:
        click.echo(click.style(f"ETHICS ERROR: {exc}", fg="red", bold=True))
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(click.style(f"Simulation error: {exc}", fg="red"))


@main.command()
@click.option("--ssid", "-s", required=True, help="Target network SSID")
@click.option("--max-attempts", "-m", default=8000, type=int)
def pmkid(ssid: str, max_attempts: int) -> None:
    """Simulate a PMKID attack (no handshake or clients required).

    Demonstrates extraction of RSN PMKID from an AP and subsequent
    offline cracking in safe simulation mode.
    """
    auditor = Auditor(simulation_mode=True)
    click.echo(click.style("\n=== PMKID ATTACK SIMULATOR ===", fg="magenta", bold=True))
    click.echo(f"Target SSID : {ssid}")
    click.echo("Technique   : PMKID extraction from AP (no clients needed)")
    click.echo("Mode        : SAFE SIMULATION ONLY")

    try:
        result = auditor.simulate_pmkid_attack(
            ssid=ssid,
            max_attempts=max_attempts,
        )
        click.echo("\n" + "=" * 60)
        if result.get("success"):
            click.echo(click.style("✅ PMKID CRACKED IN SIMULATION", fg="green", bold=True))
            click.echo(f"Password : {result.get('password')}")
        else:
            click.echo(click.style("No crack in this simulation run.", fg="yellow"))
        click.echo(f"Attempts made : {result.get('attempts', 0)}")
        click.echo(f"Time          : {result.get('duration_seconds', 0)} seconds")
        click.echo(f"Notes         : {result.get('notes', '')}")
        click.echo("\n" + click.style("PMKID RECOMMENDATIONS:", fg="cyan", bold=True))
        for rec in result.get("recommendations", []):
            click.echo(f"  • {rec}")
        click.echo("=" * 60)
    except PermissionError as exc:
        click.echo(click.style(f"ETHICS GUARD: {exc}", fg="red", bold=True))
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(click.style(f"Simulation error: {exc}", fg="red"))


@main.command()
@click.option("--ssid", "-s", default=None, help="Target SSID (optional)")
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    help="Output .22000 file (auto-generated if omitted)",
)
def hashcat(ssid: Optional[str], output: Optional[str]) -> None:
    """Export data for offline cracking with hashcat.

    Generates a .22000 file (modern hashcat format) containing
    illustrative hashes and detailed instructions. For real captures
    combine with hcxpcapngtool. Only use in authorized engagements.
    """
    auditor = Auditor(simulation_mode=True)
    click.echo(click.style("\n=== HASHCAT OFFLINE EXPORT ===", fg="magenta", bold=True))
    click.echo("Mode        : SAFE SIMULATION + HASHCAT PREP")
    if ssid:
        click.echo(f"Target SSID : {ssid}")

    try:
        path = auditor.export_for_hashcat(
            ssid=ssid,
            output_path=output,
        )
        click.echo("\n" + "=" * 60)
        click.echo(click.style("✅ HASHCAT FILE GENERATED SUCCESSFULLY", fg="green", bold=True))
        click.echo(f"Location : {path}")
        click.echo("\nUse with:")
        click.echo(f"  hashcat -m 22000 {Path(path).name} wordlist.txt")
        click.echo("\nOpen the generated file for full instructions on real captures.")
        click.echo("=" * 60)
    except PermissionError as exc:
        click.echo(click.style(f"ETHICS GUARD: {exc}", fg="red", bold=True))
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(click.style(f"Export error: {exc}", fg="red"))


@main.command()
@click.option(
    "--title",
    default="WaveBrute Ethical Audit Report",
    help="Title for the generated PDF",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    help="Output PDF path (auto-generated if omitted)",
)
def report(title: str, output: Optional[str]) -> None:
    """Generate a professional PDF report from collected audit results.

    If no prior results exist a small simulation pipeline is run automatically
    so the command is always runnable.
    """
    auditor = Auditor(simulation_mode=True)
    # Ensure we have data for the report
    if not auditor.get_results():
        click.echo("No prior results found — running quick simulation pipeline...")
        auditor.scan()
        auditor.simulate_attack("Cafe_Rouge_FreeWiFi")
        auditor.simulate_pmkid_attack("IoT-Devices")
        auditor.analyze_handshake("demo.cap")  # will simulate
        auditor.export_for_hashcat("Cafe_Rouge_FreeWiFi")

    click.echo(click.style("\n=== REPORT BUILDER ===", fg="magenta", bold=True))
    click.echo(f"Title : {title}")

    try:
        pdf_path = auditor.build_report(title=title, output_path=output)
        click.echo(click.style("\nPDF REPORT GENERATED SUCCESSFULLY", fg="green", bold=True))
        click.echo(f"Location : {pdf_path}")
        click.echo("\nThe PDF uses neo-brutalist styling (thick borders, #ff004d/#00ff9f accents).")
        click.echo("Open it with any PDF viewer. All actions were simulated.")
    except ValueError as exc:
        click.echo(click.style(f"Report error: {exc}", fg="red"))
    except Exception as exc:  # pylint: disable=broad-except
        click.echo(click.style(f"Unexpected error: {exc}", fg="red"))


@main.command()
def ethics() -> None:
    """Show the mandatory ethics & legal consent checklist."""
    from .ethics import ConsentManager
    cm = ConsentManager()
    cm.show_checklist()


if __name__ == "__main__":
    main()

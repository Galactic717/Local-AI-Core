"""
VRAM Monitor - Real-time VRAM usage dashboard
==============================================
Консольний дашборд з кольоровим виводом
"""

import time
import requests
import subprocess
from datetime import datetime

# ANSI color codes
RED = '\033[91m'
YELLOW = '\033[93m'
GREEN = '\033[92m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

ORCHESTRATOR_URL = "http://localhost:8004"

def clear_screen():
    """Clear console screen"""
    subprocess.run('cls', shell=True)

def get_status():
    """Get VRAM status from orchestrator"""
    try:
        response = requests.get(f"{ORCHESTRATOR_URL}/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def get_color(status: str) -> str:
    """Get color based on status"""
    if status == 'critical':
        return RED
    elif status == 'warning':
        return YELLOW
    else:
        return GREEN

def draw_bar(percent: float, width: int = 40) -> str:
    """Draw progress bar"""
    filled = int(width * percent / 100)
    bar = '█' * filled + '░' * (width - filled)

    if percent > 90:
        color = RED
    elif percent > 80:
        color = YELLOW
    else:
        color = GREEN

    return f"{color}{bar}{RESET}"

def emergency_unload():
    """Emergency unload all models"""
    try:
        print(f"\n{RED}🚨 EMERGENCY UNLOAD TRIGGERED!{RESET}")
        response = requests.post(f"{ORCHESTRATOR_URL}/unload/all", timeout=10)
        if response.status_code == 200:
            print(f"{GREEN}✅ All models unloaded{RESET}")
        else:
            print(f"{RED}❌ Unload failed{RESET}")
    except Exception as e:
        print(f"{RED}❌ Error: {e}{RESET}")

def main():
    """Main monitoring loop"""
    print(f"{BOLD}{CYAN}VRAM Monitor - Press Ctrl+C to exit{RESET}\n")

    consecutive_critical = 0

    try:
        while True:
            clear_screen()

            # Header
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"{BOLD}{CYAN}╔════════════════════════════════════════════════════════════╗{RESET}")
            print(f"{BOLD}{CYAN}║         LOCAL AI ASSISTANT - VRAM MONITOR                  ║{RESET}")
            print(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════╝{RESET}")
            print(f"  {now}\n")

            # Get status
            status = get_status()

            if status is None:
                print(f"{RED}❌ Cannot connect to Orchestrator (port 8004){RESET}")
                print(f"\n{YELLOW}Make sure orchestrator is running:{RESET}")
                print(f"  cd E:\\projects\\AI\\local-ai-assistant")
                print(f"  venv\\Scripts\\python services\\orchestrator.py")
                time.sleep(5)
                continue

            # VRAM usage
            used = status['used_mb']
            total = status['total_mb']
            free = status['free_mb']
            percent = status['percent']
            threshold = status['threshold_mb']
            warning = status['warning_mb']
            critical = status['critical_mb']
            vram_status = status['status']

            color = get_color(vram_status)

            print(f"{BOLD}VRAM Usage:{RESET}")
            print(f"  {draw_bar(percent)} {percent:.1f}%")
            print(f"  {color}{used} MB{RESET} / {total} MB  (Free: {free} MB)\n")

            # Thresholds
            print(f"{BOLD}Thresholds:{RESET}")
            print(f"  {GREEN}Normal:{RESET}    < {warning} MB")
            print(f"  {YELLOW}Warning:{RESET}   {warning} - {threshold} MB")
            print(f"  {RED}Critical:{RESET}  > {threshold} MB (Emergency: {critical} MB)\n")

            # Status
            print(f"{BOLD}Status:{RESET} ", end="")
            if vram_status == 'ok':
                print(f"{GREEN}✅ OK{RESET}")
            elif vram_status == 'warning':
                print(f"{YELLOW}⚠️  WARNING{RESET}")
            else:
                print(f"{RED}🚨 CRITICAL{RESET}")

            print()

            # Loaded models
            models = status.get('loaded_models', [])
            print(f"{BOLD}Loaded Models:{RESET} {len(models)}")
            if models:
                for model in models:
                    print(f"  • {model}")
            else:
                print(f"  {CYAN}(none){RESET}")

            print()

            # Critical alert
            if used > threshold:
                consecutive_critical += 1
                print(f"{RED}{BOLD}⚠️  VRAM EXCEEDS THRESHOLD!{RESET}")
                print(f"{RED}   {used} MB > {threshold} MB{RESET}")

                if consecutive_critical >= 3:
                    print(f"\n{RED}{BOLD}🚨 CRITICAL: 3 consecutive threshold violations!{RESET}")
                    emergency_unload()
                    consecutive_critical = 0
                    time.sleep(3)
            else:
                consecutive_critical = 0

            # Footer
            print(f"\n{CYAN}{'─' * 60}{RESET}")
            print(f"{CYAN}Refreshing every 1 second... Press Ctrl+C to exit{RESET}")

            time.sleep(1)

    except KeyboardInterrupt:
        print(f"\n\n{GREEN}Monitor stopped.{RESET}")

if __name__ == "__main__":
    main()

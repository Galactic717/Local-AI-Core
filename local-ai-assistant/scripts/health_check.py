"""
Health Check - Verify all services are running
===============================================
Перевірка портів та статусу сервісів
"""

import requests
import socket
from typing import Dict, Tuple

# ANSI colors
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'
BOLD = '\033[1m'

SERVICES = {
    'Ollama': ('localhost', 11434, 'http://localhost:11434/api/tags'),
    'Orchestrator': ('localhost', 8004, 'http://localhost:8004/health'),
    'STT Service': ('localhost', 8001, 'http://localhost:8001/health'),
    'TTS Service': ('localhost', 8002, 'http://localhost:8002/health'),
    'Image Service': ('localhost', 8003, 'http://localhost:8003/health'),
    'WebUI': ('localhost', 8080, 'http://localhost:8080'),
}

def check_port(host: str, port: int, timeout: float = 2.0) -> bool:
    """Check if port is open"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_http(url: str, timeout: float = 2.0) -> Tuple[bool, int]:
    """Check HTTP endpoint"""
    try:
        response = requests.get(url, timeout=timeout)
        return True, response.status_code
    except:
        return False, 0

def get_vram_status() -> Dict:
    """Get VRAM status from orchestrator"""
    try:
        response = requests.get('http://localhost:8004/status', timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {}

def main():
    """Run health check"""
    print(f"{BOLD}{CYAN}╔════════════════════════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{CYAN}║         LOCAL AI ASSISTANT - HEALTH CHECK                  ║{RESET}")
    print(f"{BOLD}{CYAN}╚════════════════════════════════════════════════════════════╝{RESET}\n")

    all_ok = True

    # Check services
    print(f"{BOLD}Services:{RESET}\n")

    for name, (host, port, url) in SERVICES.items():
        port_open = check_port(host, port)
        http_ok, status_code = check_http(url)

        if port_open and http_ok:
            print(f"  {GREEN}✅{RESET} {name:20} Port {port:5} {GREEN}OK{RESET} (HTTP {status_code})")
        elif port_open:
            print(f"  {YELLOW}⚠️ {RESET} {name:20} Port {port:5} {YELLOW}OPEN{RESET} (HTTP failed)")
            all_ok = False
        else:
            print(f"  {RED}❌{RESET} {name:20} Port {port:5} {RED}CLOSED{RESET}")
            all_ok = False

    print()

    # VRAM status
    vram = get_vram_status()
    if vram:
        print(f"{BOLD}VRAM Status:{RESET}\n")
        used = vram['used_mb']
        total = vram['total_mb']
        percent = vram['percent']
        status = vram['status']

        if status == 'ok':
            color = GREEN
            icon = '✅'
        elif status == 'warning':
            color = YELLOW
            icon = '⚠️ '
        else:
            color = RED
            icon = '🚨'
            all_ok = False

        print(f"  {icon} {color}{used} MB{RESET} / {total} MB ({percent:.1f}%)")
        print(f"  Status: {color}{status.upper()}{RESET}")

        models = vram.get('loaded_models', [])
        if models:
            print(f"  Loaded: {', '.join(models)}")
        else:
            print(f"  Loaded: {CYAN}(none){RESET}")
    else:
        print(f"{BOLD}VRAM Status:{RESET}\n")
        print(f"  {RED}❌ Cannot get VRAM status{RESET}")
        all_ok = False

    print()

    # Summary
    print(f"{CYAN}{'─' * 60}{RESET}")
    if all_ok:
        print(f"\n{GREEN}{BOLD}✅ All systems operational!{RESET}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}❌ Some services are down or degraded{RESET}\n")
        return 1

if __name__ == "__main__":
    exit(main())

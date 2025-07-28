import subprocess
import time
import datetime
import re
import signal
import sys
import statistics
import argparse
import msvcrt  # Windows-only
from colorama import init as colorama_init, Fore, Style

# Enable ANSI color output
colorama_init()

# Defaults
HOST = "8.8.8.8"
PING_INTERVAL = 1
RTT_THRESHOLD_MS = 100
LOG_FILE = "ping_log.txt"
MAX_PINGS = None

# Runtime state
ping_count = 0
logged_count = 0
total_rtt = 0
total_ttl = 0
valid_rtt_count = 0
valid_ttl_count = 0
rtt_list = []
min_rtt = None
max_rtt = None
running = True
paused = False

def log_event(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(full_message + "\n")

def print_status():
    avg_rtt = total_rtt / valid_rtt_count if valid_rtt_count else 0
    avg_ttl = total_ttl / valid_ttl_count if valid_ttl_count else 0
    median_rtt = statistics.median(rtt_list) if rtt_list else 0
    percent_logged = (logged_count / ping_count * 100) if ping_count > 0 else 0

    pause_status = " (paused)" if paused else ""
    rtt_ext = f"(min {min_rtt}, max {max_rtt})" if min_rtt is not None and max_rtt is not None else ""

    if MAX_PINGS is not None:
        ping_info = f"Pings: {ping_count}/{MAX_PINGS}"
    else:
        ping_info = f"Pings: {ping_count}"

    status = (
        f"{ping_info} | Logged: {logged_count} ({percent_logged:.1f}%) | "
        f"RTT avg: {avg_rtt:.1f} ms, med: {median_rtt:.1f} {rtt_ext} | "
        f"TTL avg: {avg_ttl:.1f}{pause_status}"
    )

    # Pad the line to fully overwrite previous content
    clean_line = f"\r{status:<120}"  # Adjust width as needed

    if paused:
        sys.stdout.write(Fore.RED + clean_line + Style.RESET_ALL)
    else:
        sys.stdout.write(clean_line)
    sys.stdout.flush()

def parse_ping_output(output):
    if "Request timed out." in output or "Destination host unreachable" in output:
        return "timeout", None, None

    rtt_match = re.search(r"Average = (\d+)ms", output)
    ttl_match = re.search(r"TTL=(\d+)", output)

    rtt = int(rtt_match.group(1)) if rtt_match else None
    ttl = int(ttl_match.group(1)) if ttl_match else None

    if rtt is not None:
        return "success", rtt, ttl
    return "unknown", None, None

def handle_sigint(signal_received, frame):
    global running
    print("\nStopping ping monitor...")
    avg_rtt = total_rtt / valid_rtt_count if valid_rtt_count else 0
    median_rtt = statistics.median(rtt_list) if rtt_list else 0
    avg_ttl = total_ttl / valid_ttl_count if valid_ttl_count else 0
    percent_logged = (logged_count / ping_count * 100) if ping_count > 0 else 0

    log_event(
        f"Monitor stopped. Total pings: {ping_count}, Logged: {logged_count} ({percent_logged:.1f}%), "
        f"Avg RTT: {avg_rtt:.1f}, Median RTT: {median_rtt:.1f}, Min RTT: {min_rtt}, Max RTT: {max_rtt}, "
        f"Avg TTL: {avg_ttl:.1f}"
    )
    print(
        f"Final summary -> Pings: {ping_count}, Logged: {logged_count} ({percent_logged:.1f}%), "
        f"Avg RTT: {avg_rtt:.1f} ms, Median RTT: {median_rtt:.1f}, "
        f"Min RTT: {min_rtt}, Max RTT: {max_rtt}, Avg TTL: {avg_ttl:.1f}"
    )
    running = False

def check_keyboard_input():
    global paused
    if msvcrt.kbhit():
        key = msvcrt.getwch()
        if key.lower() == 'p':
            paused = not paused
            log_event("Ping monitor paused" if paused else "Ping monitor resumed")
            print_status()

def ping_loop():
    global ping_count, logged_count, total_rtt, total_ttl
    global valid_rtt_count, valid_ttl_count, min_rtt, max_rtt, rtt_list, running

    log_event(f"Starting ping monitor for {HOST}...")
    while running:
        check_keyboard_input()

        if paused:
            print_status()
            time.sleep(0.1)
            continue

        try:
            result = subprocess.run(
                ["ping", "-n", "1", HOST],
                capture_output=True,
                text=True,
                timeout=5
            )
            ping_count += 1
            status, rtt, ttl = parse_ping_output(result.stdout)

            if status == "timeout":
                log_event("Ping timeout")
                logged_count += 1
            elif status == "success":
                if rtt > RTT_THRESHOLD_MS:
                    log_event(f"High RTT: {rtt} ms")
                    logged_count += 1
                if rtt is not None:
                    total_rtt += rtt
                    valid_rtt_count += 1
                    rtt_list.append(rtt)
                    if min_rtt is None or rtt < min_rtt:
                        min_rtt = rtt
                    if max_rtt is None or rtt > max_rtt:
                        max_rtt = rtt
                if ttl is not None:
                    total_ttl += ttl
                    valid_ttl_count += 1
            else:
                log_event("Ping result could not be parsed")
                logged_count += 1

        except subprocess.TimeoutExpired:
            log_event("Ping command itself timed out")
            logged_count += 1
        except Exception as e:
            log_event(f"Error during ping: {e}")
            logged_count += 1

        print_status()

        if MAX_PINGS is not None and ping_count >= MAX_PINGS:
            handle_sigint(None, None)
            break

        for _ in range(int(PING_INTERVAL * 10)):
            time.sleep(0.1)
            check_keyboard_input()
            if paused or not running:
                break

def print_help_and_exit():
    help_text = """
Ping Monitor with Logging and Pause Support

Usage:
    python betterping.py [options]

Options:
    --help            Show this help message and exit.
    --s HOST          Set the target server to ping (default: 8.8.8.8).
    --t N             Set delay between pings in seconds (default: 1).
    --limit N         Set RTT logging threshold in ms (default: 100).
    --log FILE        Set logfile name (default: ping_log.txt).
    --n N             Exit after N total pings.
    Press "P"         While running, press P to pause or resume pinging.
"""
    print(help_text)
    sys.exit(0)

# --- Entry Point ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--help", action="store_true")
    parser.add_argument("--s", type=str)
    parser.add_argument("--t", type=float)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--log", type=str)
    parser.add_argument("--n", type=int)

    try:
        args = parser.parse_args()
    except SystemExit as e:
        print("Illegal or unrecognized flag. Use: python betterping.py --help")
        sys.exit(1)

    if args.help:
        print_help_and_exit()
    if args.s:
        HOST = args.s
    if args.t:
        PING_INTERVAL = args.t
    if args.limit:
        RTT_THRESHOLD_MS = args.limit
    if args.log:
        LOG_FILE = args.log
    if args.n is not None:
        MAX_PINGS = args.n

    signal.signal(signal.SIGINT, handle_sigint)

    try:
        ping_loop()
    except Exception as e:
        log_event(f"Unexpected error: {e}")
        print(f"\nError: {e}")

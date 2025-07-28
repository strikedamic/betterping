# betterping

A robust, colorized single-line ping monitor for Windows with logging, statistics, and pause/resume support.

## Features
- Pings a target host at a configurable interval
- Logs high-latency and failed (lost) pings to a file with timestamps
- Tracks and displays statistics: average, median, min/max RTT, TTL, and percent logged
- Colorized, live-updating status line in the terminal
- Pause/resume monitoring with the `P` key (no data lost)
- Graceful shutdown with summary on Ctrl+C
- Configurable via command-line options

## Requirements
- Windows (uses `msvcrt` and Windows `ping`)
- Python 3.6+
- [colorama](https://pypi.org/project/colorama/)

## Installation
1. Place `betterping.py` anywhere on your system.
2. Install dependencies:
   ```sh
   pip install colorama
   ```

## Usage
```sh
python betterping.py [options]
```

### Options
- `--help`            Show help message and exit
- `--s HOST`          Set the target server to ping (default: 8.8.8.8)
- `--t N`             Set delay between pings in seconds (default: 1)
- `--limit N`         Set RTT logging threshold in ms (default: 100)
- `--log FILE`        Set logfile name (default: ping_log.txt)
- `--n N`             Exit after N total pings

While running, press `P` to pause or resume pinging.

## Logging
- All high-latency pings (RTT > threshold) and all failed/lost pings are logged to the specified log file with timestamps.
- A summary is logged on exit (Ctrl+C).

## Example
```sh
python betterping.py --s 1.1.1.1 --t 0.5 --limit 80 --log mylog.txt --n 100
```

## License
GNU V3.0 

## AI Disclaimer
This software was created using Artificial Intelligence agents (Claude v4 within Cursor IDE)

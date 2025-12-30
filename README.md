# Paro-framwork-
PARO-ULTRA: Autonomous AI Pentesting Framework for External Asset Discovery &amp; Vulnerability Scanning. Integrates 10+ tools (Nuclei, Nmap, etc.) with stealth evasion, real-time dashboard, and 3000+ vuln detection.









# PARO-ULTRA: Autonomous AI Pentesting Framework

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-lightgrey)](https://flask.palletsprojects.com/)

PARO-ULTRA is an advanced, autonomous AI-driven pentesting framework built in Python/Flask. It automates external asset discovery, WAF-aware scanning, and vulnerability detection across 1000+ network and 3000+ web vulnerabilities. Designed for security professionals, it integrates open-source tools like Nuclei, Nmap, and more, with built-in stealth (random delays, User-Agent rotation) and a real-time dark-mode dashboard for monitoring.

## Features

- **Automated Discovery**: Passive subdomain enumeration using `subfinder`, `assetfinder`, and `amass`.
- **Health Checks & WAF Analysis**: Filters live assets with `httpx` and detects/bypasses WAFs (e.g., Cloudflare, Akamai) using `wafw00f`.
- **Deep Crawling**: Extracts URLs via `waybackurls` and `katana`.
- **Pattern Matching**: Pure Python regex for categorizing URLs (SQLi, XSS, LFI, Redirect).
- **Vulnerability Scanning**: Targeted scans with `dalfox` (XSS), `nuclei` (full templates), `nikto`, `sstimap`, and `nmap` (NSE scripts).
- **Stealth & Evasion**: Random delays, User-Agent rotation, and automatic scan reduction for protected targets.
- **Real-Time Dashboard**: Flask-based UI with live logs, counters (subdomains/URLs/vulns), and findings table.
- **Concurrency**: Background threading with proper Flask app context handling.
- **Error Handling**: Robust subprocess management with timeouts and graceful tool skipping.
- **Export**: JSON report export for findings.

## Architecture

- **Backend**: Python 3.x + Flask (web server), SQLAlchemy (SQLite DB).
- **Frontend**: HTML5 + Bootstrap 5 (dark-mode dashboard), JavaScript (Fetch API for real-time updates).
- **Tools Integration**: Wrapper for 10+ external tools via subprocess calls.
- **Database Models**: `Target`, `Subdomain`, `Url`, `Vulnerability` for persistent storage.
- **Phased Workflow**:
  1. Discovery (Subdomains).
  2. WAF Analysis (Stealth filtering).
  3. Crawling (URL extraction).
  4. Pattern Matching (Regex categorization).
  5. Scanning (Targeted vulns).

## Installation

### Prerequisites
- Linux/macOS/Windows (with WSL for Windows).
- Python 3.8+.
- Go 1.19+ (for installing tools).
- Git.

### Step-by-Step Installation
1. **Clone the Repository**:

2. git clone https://github.com/Vishal8736/Paro-framwork-

3. python3 -c "import flask, flask_sqlalchemy, requests; print('Python deps OK')"

4. 
4. **Install External Tools**:
- Add `~/go/bin` to PATH: `export PATH=$PATH:~/go/bin` (add to ~/.bashrc).

- Verify: `which subfinder assetfinder amass httpx wafw00f waybackurls katana dalfox nuclei nikto sstimap`

5. **Update Nuclei Path**: In `audit_engine.py`, replace `/path/to/nuclei-templates` with `~/.nuclei-templates`.

## Usage

1. **Run the Application**:

2. - Access the dashboard at `http://localhost:5000`.

2. **Start a Scan**:
- Enter a target domain (e.g., `example.com`).
- Click "Start Audit".
- Monitor real-time logs, counters, and findings.

3. **Export Report**:
- Click "Export Report" to download a JSON file of vulnerabilities.

4. **Stop/Resume**: Use "Stop Task" to halt background scans.

### Example Workflow
- Input: `company.com`
- Output: Discovers subdomains, filters WAF-protected ones, crawls URLs, matches patterns, scans for vulns, and displays results in the dashboard.

## Screenshots
*(Add images here, e.g., dashboard view)*

## Contributing
Contributions are welcome! Please:
1. Fork the repo.
2. Create a feature branch.
3. Submit a pull request with tests.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer
PARO-ULTRA is for educational and authorized security testing only. Use on unauthorized targets is illegal. The authors are not responsible for misuse. Always obtain written permission before scanning.

## Contact
- Author: [Your Name](https://github.com/yourusername)
- Issues: [GitHub Issues](https://github.com/yourusername/paro-ultra/issues)


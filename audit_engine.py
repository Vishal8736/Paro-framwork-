import subprocess
import json
import re
import time
import random
import requests
from models import db, Target, Subdomain, Url, Vulnerability

class AuditEngine:
    def __init__(self, domain, log_queue, app):
        self.domain = domain
        self.log_queue = log_queue
        self.app = app
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            # Add more as needed
        ]
        self.current_ua = 0

    def log(self, message):
        self.log_queue.put(f"[INFO] {message}")

    def get_user_agent(self):
        ua = self.user_agents[self.current_ua % len(self.user_agents)]
        self.current_ua += 1
        return ua

    def run_subprocess(self, cmd, description, input_data=None):
        try:
            self.log(f"Running {description}...")
            time.sleep(random.uniform(1, 5))  # Stealth delay
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300, input=input_data)
            if result.returncode != 0:
                self.log(f"{description} failed: {result.stderr}")
                return None
            self.log(f"{description} completed.")
            return result.stdout
        except FileNotFoundError:
            self.log(f"Tool for {description} not found. Skipping.")
            return None
        except subprocess.TimeoutExpired:
            self.log(f"{description} timed out. Killing.")
            return None
        except Exception as e:
            self.log(f"Error in {description}: {str(e)}")
            return None

    def run(self):
        with self.app.app_context():
            self.log("Starting PARO-ULTRA audit for domain: " + self.domain)
            
            # Create Target
            target = Target.query.filter_by(domain=self.domain).first()
            if not target:
                target = Target(domain=self.domain)
                db.session.add(target)
                db.session.commit()
            
            # Phase 1: Discovery
            subdomains = set()
            output = self.run_subprocess(['subfinder', '-d', self.domain, '-silent'], "Passive subdomain discovery with subfinder")
            if output:
                subdomains.update(line.strip() for line in output.split('\n') if line.strip())
            output = self.run_subprocess(['assetfinder', '--subs-only', self.domain], "Passive subdomain discovery with assetfinder")
            if output:
                subdomains.update(line.strip() for line in output.split('\n') if line.strip())
            output = self.run_subprocess(['amass', 'enum', '-passive', '-d', self.domain], "Passive subdomain discovery with amass")
            if output:
                subdomains.update(line.strip() for line in output.split('\n') if line.strip())
            
            for sub in subdomains:
                subdomain = Subdomain(target_id=target.id, subdomain=sub)
                db.session.add(subdomain)
            db.session.commit()
            self.log(f"Discovery complete. Found {len(subdomains)} subdomains.")
            
            # Filter live with httpx
            subdomains_db = Subdomain.query.filter_by(target_id=target.id).all()
            for sub in subdomains_db:
                ua = self.get_user_agent()
                output = self.run_subprocess(['httpx', '-u', f"https://{sub.subdomain}", '-H', f"User-Agent: {ua}", '-status-code'], "Health check with httpx")
                if output and any(code in output for code in ['200', '301', '403']):
                    sub.is_live = True
            db.session.commit()
            live_subs = [s for s in subdomains_db if s.is_live]
            self.log(f"Live subdomains: {len(live_subs)}")
            
            # Phase 2: Intelligent WAF Analysis
            for sub in live_subs:
                output = self.run_subprocess(['wafw00f', f"https://{sub.subdomain}"], "WAF detection with wafw00f")
                waf = 'No WAF'
                if output:
                    if 'Cloudflare' in output or 'Akamai' in output:
                        waf = 'Non-Bypassable'
                        self.log(f"Non-bypassable WAF detected for {sub.subdomain}. Aborting scan for stealth.")
                        continue  # Skip this subdomain
                    elif 'WAF' in output:
                        waf = 'Bypassable'
                sub.waf_status = waf
            db.session.commit()
            eligible_subs = [s for s in live_subs if s.waf_status in ['No WAF', 'Bypassable']]
            self.log(f"Eligible subdomains after WAF check: {len(eligible_subs)}")
            
            # Phase 3: Deep Crawling
            for sub in eligible_subs:
                urls = set()
                output = self.run_subprocess(['waybackurls', f"https://{sub.subdomain}"], "URL extraction with waybackurls")
                if output:
                    urls.update(line.strip() for line in output.split('\n') if line.strip())
                output = self.run_subprocess(['katana', '-u', f"https://{sub.subdomain}"], "URL extraction with katana")
                if output:
                    urls.update(line.strip() for line in output.split('\n') if line.strip())
                for u in urls:
                    url = Url(subdomain_id=sub.id, url=u)
                    db.session.add(url)
            db.session.commit()
            self.log("Deep crawling complete.")
            
            # Phase 4: Pattern Matching (Pure Python Regex)
            urls_db = Url.query.filter(Url.subdomain_id.in_([s.id for s in eligible_subs])).all()
            for url_obj in urls_db:
                url = url_obj.url
                if re.search(r'\b(id|select)=\w+', url, re.IGNORECASE):
                    url_obj.category = 'SQLi'
                elif re.search(r'\b(q|search)=\w+', url, re.IGNORECASE):
                    url_obj.category = 'XSS'
                elif re.search(r'\b(file|path)=\w+', url, re.IGNORECASE):
                    url_obj.category = 'LFI'
                elif re.search(r'\b(url|next)=\w+', url, re.IGNORECASE):
                    url_obj.category = 'Redirect'
                else:
                    url_obj.category = 'None'
            db.session.commit()
            self.log("Pattern matching complete.")
            
            # Phase 5: Targeted Vulnerability Scanning
            xss_urls = [u for u in urls_db if u.category == 'XSS']
            sqli_lfi_urls = [u for u in urls_db if u.category in ['SQLi', 'LFI']]
            
            # XSS with dalfox
            for url_obj in xss_urls:
                output = self.run_subprocess(['dalfox', 'url', url_obj.url], "XSS scanning with dalfox")
                if output:
                    # Parse dalfox output (assume JSON; adjust if needed)
                    try:
                        findings = json.loads(output)
                        for finding in findings:
                            vuln = Vulnerability(
                                url_id=url_obj.id,
                                tool='dalfox',
                                severity=finding.get('severity', 'unknown'),
                                name=finding.get('type', 'XSS'),
                                description=finding.get('payload', 'N/A')
                            )
                            db.session.add(vuln)
                    except:
                        self.log("Failed to parse dalfox output.")
            
            # SQLi/LFI with nuclei
            for url_obj in sqli_lfi_urls:
                tag = 'sqli' if url_obj.category == 'SQLi' else 'lfi'
                output = self.run_subprocess(['nuclei', '-u', url_obj.url, '-tags', tag, '-json'], f"{tag.upper()} scanning with nuclei")
                if output:
                    for line in output.strip().split('\n'):
                        try:
                            finding = json.loads(line)
                            vuln = Vulnerability(
                                url_id=url_obj.id,
                                tool='nuclei',
                                severity=finding.get('info', {}).get('severity', 'unknown'),
                                name=finding.get('info', {}).get('name', 'Unknown'),
                                description=finding.get('info', {}).get('description', 'N/A')
                            )
                            db.session.add(vuln)
                        except json.JSONDecodeError:
                            continue
            
            # General nuclei on main domain
            output = self.run_subprocess(['nuclei', '-u', f"https://{self.domain}", '-t', '/path/to/nuclei-templates', '-json'], "General vulnerability scanning with nuclei")
            if output:
                for line in output.strip().split('\n'):
                    try:
                        finding = json.loads(line)
                        # Associate with a dummy URL or main subdomain
                        main_sub = Subdomain.query.filter_by(target_id=target.id, subdomain=self.domain).first()
                        if main_sub:
                            url_obj = Url.query.filter_by(subdomain_id=main_sub.id, url=f"https://{self.domain}").first()
                            if not url_obj:
                                url_obj = Url(subdomain_id=main_sub.id, url=f"https://{self.domain}")
                                db.session.add(url_obj)
                                db.session.commit()
                            vuln = Vulnerability(
                                url_id=url_obj.id,
                                tool='nuclei',
                                severity=finding.get('info', {}).get('severity', 'unknown'),
                                name=finding.get('info', {}).get('name', 'Unknown'),
                                description=finding.get('info', {}).get('description', 'N/A')
                            )
                            db.session.add(vuln)
                    except json.JSONDecodeError:
                        continue
            
            # Deep scans with nikto and sstimap on high-probability targets (e.g., live subs)
            for sub in eligible_subs[:5]:  # Limit to top 5 for performance
                output = self.run_subprocess(['nikto', '-h', f"https://{sub.subdomain}"], "Deep scan with nikto")
                if output:
                    # Parse nikto output (simple text parsing)
                    for line in output.split('\n'):
                        if 'Vulnerability' in line:
                            vuln = Vulnerability(
                                url_id=Url.query.filter_by(subdomain_id=sub.id).first().id if Url.query.filter_by(subdomain_id=sub.id).first() else None,
                                tool='nikto',
                                severity='medium',
                                name='Nikto Finding',
                                description=line
                            )
                            db.session.add(vuln)
                output = self.run_subprocess(['sstimap', '-u', f"https://{sub.subdomain}"], "SSTi scan with sstimap")
                if output:
                    # Parse sstimap output
                    for line in output.split('\n'):
                        if 'Vulnerable' in line:
                            vuln = Vulnerability(
                                url_id=Url.query.filter_by(subdomain_id=sub.id).first().id if Url.query.filter_by(subdomain_id=sub.id).first() else None,
                                tool='sstimap',
                                severity='high',
                                name='SSTi',
                                description=line
                            )
                            db.session.add(vuln)
            
            db.session.commit()
            self.log("Audit complete.")

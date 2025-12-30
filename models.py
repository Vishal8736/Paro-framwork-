from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Target(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), nullable=False, unique=True)

class Subdomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('target.id'), nullable=False)
    subdomain = db.Column(db.String(255), nullable=False)
    is_live = db.Column(db.Boolean, default=False)
    waf_status = db.Column(db.String(100), default='Unknown')  # e.g., No WAF, Cloudflare, Bypassable

class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    subdomain_id = db.Column(db.Integer, db.ForeignKey('subdomain.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))  # SQLi, XSS, LFI, Redirect, None

class Vulnerability(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url_id = db.Column(db.Integer, db.ForeignKey('url.id'), nullable=False)
    tool = db.Column(db.String(50))  # e.g., nuclei, dalfox
    severity = db.Column(db.String(50))  # info, low, medium, high, critical
    name = db.Column(db.String(255))
    description = db.Column(db.Text)

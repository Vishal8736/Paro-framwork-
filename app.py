from flask import Flask, render_template, request, jsonify
import threading
import queue
from models import db, Target, Subdomain, Url, Vulnerability
from audit_engine import AuditEngine

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///paro_ultra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

log_queue = queue.Queue()

@app.before_first_request
def create_tables():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_scan', methods=['POST'])
def start_scan():
    domain = request.form.get('domain')
    if not domain:
        return jsonify({'error': 'Domain required'}), 400
    # Clear previous data for new scan
    while not log_queue.empty():
        log_queue.get()
    target = Target.query.filter_by(domain=domain).first()
    if target:
        Subdomain.query.filter_by(target_id=target.id).delete()
        Url.query.filter(Url.subdomain_id.in_([s.id for s in Subdomain.query.filter_by(target_id=target.id).all()])).delete()
        Vulnerability.query.filter(Vulnerability.url_id.in_([u.id for u in Url.query.filter(Url.subdomain_id.in_([s.id for s in Subdomain.query.filter_by(target_id=target.id).all()])).all()])).delete()
        Target.query.filter_by(domain=domain).delete()
    db.session.commit()
    thread = threading.Thread(target=run_audit, args=(domain, app))
    thread.start()
    return jsonify({'status': 'started'})

def run_audit(domain, app):
    engine = AuditEngine(domain, log_queue, app)
    engine.run()

@app.route('/api/stream_logs')
def stream_logs():
    logs = []
    while not log_queue.empty():
        logs.append(log_queue.get())
    return jsonify({'logs': logs})

@app.route('/api/get_counts')
def get_counts():
    subdomains = Subdomain.query.count()
    urls = Url.query.count()
    vulnerabilities = Vulnerability.query.count()
    return jsonify({'subdomains': subdomains, 'urls': urls, 'vulnerabilities': vulnerabilities})

@app.route('/api/get_deep_targets')
def get_deep_targets():
    deep_targets = Vulnerability.query.join(Url).add_columns(Url.url, Vulnerability.severity, Vulnerability.name, Vulnerability.description).all()
    data = [{'url': dt[1], 'severity': dt[2], 'name': dt[3], 'description': dt[4]} for dt in deep_targets]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)

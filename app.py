"""
Job Shop Scheduler — Application Flask principale
Point d'entrée : python app.py → http://localhost:8000
"""

import os
import json
import csv
import io
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
from database.models import db, Job, Machine, Operation, Planning, PlanningOperation, Contrainte, HistoriqueAlerte
from backend.scheduler import run_spt, run_lpt, run_edd, run_genetic
from backend.kpis import compute_kpis
from backend.alerts import check_alerts, get_unread_alerts, mark_alert_read
from backend.import_export import export_excel, export_pdf_report, import_jobs_csv
from database.seed import seed_database

# ─── App Setup ──────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "frontend", "templates"),
    static_folder=os.path.join(BASE_DIR, "frontend", "static"),
)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'scheduler.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "shopscheduler-secret-2026"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload

CORS(app)
db.init_app(app)

# ─── Init DB ─────────────────────────────────────────────────────────────────
with app.app_context():
    db.create_all()
    seed_database(db)

# ═══════════════════════════════════════════════════════════════════════════════
# FRONTEND
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/")
def index():
    return render_template("index.html")

# ═══════════════════════════════════════════════════════════════════════════════
# API — JOBS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    jobs = Job.query.order_by(Job.priorite.desc(), Job.date_creation.desc()).all()
    return jsonify([j.to_dict() for j in jobs])

@app.route("/api/jobs", methods=["POST"])
def create_job():
    data = request.get_json()
    job = Job(
        nom=data["nom"],
        priorite=data.get("priorite", 2),
        date_due=datetime.fromisoformat(data["date_due"]) if data.get("date_due") else None,
        statut=data.get("statut", "en_attente"),
    )
    db.session.add(job)
    db.session.commit()
    check_alerts(db)
    return jsonify(job.to_dict()), 201

@app.route("/api/jobs/<int:job_id>", methods=["GET"])
def get_job(job_id):
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict())

@app.route("/api/jobs/<int:job_id>", methods=["PUT"])
def update_job(job_id):
    job = Job.query.get_or_404(job_id)
    data = request.get_json()
    job.nom = data.get("nom", job.nom)
    job.priorite = data.get("priorite", job.priorite)
    job.statut = data.get("statut", job.statut)
    if data.get("date_due"):
        job.date_due = datetime.fromisoformat(data["date_due"])
    db.session.commit()
    check_alerts(db)
    return jsonify(job.to_dict())

@app.route("/api/jobs/<int:job_id>", methods=["DELETE"])
def delete_job(job_id):
    job = Job.query.get_or_404(job_id)
    Operation.query.filter_by(job_id=job_id).delete()
    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "Job supprimé"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — MACHINES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/machines", methods=["GET"])
def get_machines():
    machines = Machine.query.order_by(Machine.nom).all()
    return jsonify([m.to_dict() for m in machines])

@app.route("/api/machines", methods=["POST"])
def create_machine():
    data = request.get_json()
    machine = Machine(
        nom=data["nom"],
        type=data.get("type", "standard"),
        capacite=data.get("capacite", 1),
        statut=data.get("statut", "disponible"),
        temps_setup=data.get("temps_setup", 0),
    )
    db.session.add(machine)
    db.session.commit()
    return jsonify(machine.to_dict()), 201

@app.route("/api/machines/<int:machine_id>", methods=["GET"])
def get_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    return jsonify(machine.to_dict())

@app.route("/api/machines/<int:machine_id>", methods=["PUT"])
def update_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    data = request.get_json()
    machine.nom = data.get("nom", machine.nom)
    machine.type = data.get("type", machine.type)
    machine.capacite = data.get("capacite", machine.capacite)
    machine.statut = data.get("statut", machine.statut)
    machine.temps_setup = data.get("temps_setup", machine.temps_setup)
    db.session.commit()
    check_alerts(db)
    return jsonify(machine.to_dict())

@app.route("/api/machines/<int:machine_id>", methods=["DELETE"])
def delete_machine(machine_id):
    machine = Machine.query.get_or_404(machine_id)
    Operation.query.filter_by(machine_id=machine_id).delete()
    db.session.delete(machine)
    db.session.commit()
    return jsonify({"message": "Machine supprimée"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/operations", methods=["GET"])
def get_operations():
    ops = Operation.query.order_by(Operation.job_id, Operation.ordre).all()
    return jsonify([o.to_dict() for o in ops])

@app.route("/api/operations", methods=["POST"])
def create_operation():
    data = request.get_json()
    op = Operation(
        job_id=data["job_id"],
        machine_id=data["machine_id"],
        duree=data["duree"],
        ordre=data.get("ordre", 1),
        statut=data.get("statut", "en_attente"),
    )
    db.session.add(op)
    db.session.commit()
    return jsonify(op.to_dict()), 201

@app.route("/api/operations/<int:op_id>", methods=["GET"])
def get_operation(op_id):
    op = Operation.query.get_or_404(op_id)
    return jsonify(op.to_dict())

@app.route("/api/operations/<int:op_id>", methods=["PUT"])
def update_operation(op_id):
    op = Operation.query.get_or_404(op_id)
    data = request.get_json()
    op.job_id = data.get("job_id", op.job_id)
    op.machine_id = data.get("machine_id", op.machine_id)
    op.duree = data.get("duree", op.duree)
    op.ordre = data.get("ordre", op.ordre)
    op.statut = data.get("statut", op.statut)
    db.session.commit()
    return jsonify(op.to_dict())

@app.route("/api/operations/<int:op_id>", methods=["DELETE"])
def delete_operation(op_id):
    op = Operation.query.get_or_404(op_id)
    db.session.delete(op)
    db.session.commit()
    return jsonify({"message": "Opération supprimée"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — SCHEDULING
# ═══════════════════════════════════════════════════════════════════════════════

ALGO_MAP = {
    "spt": run_spt,
    "lpt": run_lpt,
    "edd": run_edd,
    "genetic": run_genetic,
}

@app.route("/api/schedule", methods=["POST"])
def schedule():
    data = request.get_json()
    algo = data.get("algorithme", "spt").lower()

    jobs = Job.query.filter(Job.statut != "terminé").all()
    machines = Machine.query.filter(Machine.statut == "disponible").all()
    operations = Operation.query.filter(Operation.statut != "terminé").all()

    if not jobs or not machines or not operations:
        return jsonify({"error": "Pas assez de données pour planifier"}), 400

    fn = ALGO_MAP.get(algo, run_spt)
    result = fn(jobs, machines, operations)

    # Sauvegarder le planning
    kpis = compute_kpis(result["schedule"], jobs, machines)
    planning = Planning(
        nom=f"Planning {algo.upper()} — {datetime.now().strftime('%d/%m %H:%M')}",
        algorithme=algo.upper(),
        makespan=kpis["makespan"],
        taux_retard=kpis["taux_retard"],
    )
    db.session.add(planning)
    db.session.flush()

    for entry in result["schedule"]:
        po = PlanningOperation(
            planning_id=planning.id,
            operation_id=entry["operation_id"],
            heure_debut=entry["start"],
            heure_fin=entry["end"],
            machine_id=entry["machine_id"],
        )
        db.session.add(po)

    db.session.commit()
    check_alerts(db)

    return jsonify({
        "planning_id": planning.id,
        "algorithme": algo.upper(),
        "makespan": kpis["makespan"],
        "taux_retard": kpis["taux_retard"],
        "utilisation_machines": kpis["utilisation_machines"],
        "gantt": result["gantt"],
        "schedule": result["schedule"],
    })

@app.route("/api/compare", methods=["POST"])
def compare_algorithms():
    jobs = Job.query.filter(Job.statut != "terminé").all()
    machines = Machine.query.filter(Machine.statut == "disponible").all()
    operations = Operation.query.filter(Operation.statut != "terminé").all()

    if not jobs or not machines or not operations:
        return jsonify({"error": "Données insuffisantes"}), 400

    results = {}
    for algo, fn in ALGO_MAP.items():
        try:
            result = fn(jobs, machines, operations)
            kpis = compute_kpis(result["schedule"], jobs, machines)
            results[algo.upper()] = {
                "makespan": kpis["makespan"],
                "taux_retard": kpis["taux_retard"] * 100,
                "utilisation_moy": sum(kpis["utilisation_machines"].values()) / max(len(kpis["utilisation_machines"]), 1),
            }
        except Exception as e:
            results[algo.upper()] = {"error": str(e)}

    return jsonify(results)

# ═══════════════════════════════════════════════════════════════════════════════
# API — KPIs & PLANNINGS
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/kpis", methods=["GET"])
def get_kpis():
    jobs = Job.query.all()
    machines = Machine.query.all()
    operations = Operation.query.all()

    total_jobs = len(jobs)
    jobs_en_cours = sum(1 for j in jobs if j.statut == "en_cours")
    jobs_termines = sum(1 for j in jobs if j.statut == "terminé")
    jobs_retard = sum(1 for j in jobs if j.date_due and j.statut != "terminé" and j.date_due < datetime.utcnow())
    machines_dispo = sum(1 for m in machines if m.statut == "disponible")
    ops_terminees = sum(1 for o in operations if o.statut == "terminé")
    ops_total = len(operations)
    completion = round((ops_terminees / ops_total * 100) if ops_total > 0 else 0, 1)

    latest_planning = Planning.query.order_by(Planning.date_creation.desc()).first()
    makespan = latest_planning.makespan if latest_planning else 0
    taux_retard = round(latest_planning.taux_retard * 100, 1) if latest_planning else 0

    unread_alerts = HistoriqueAlerte.query.filter_by(lu=False).count()

    return jsonify({
        "total_jobs": total_jobs,
        "jobs_en_cours": jobs_en_cours,
        "jobs_termines": jobs_termines,
        "jobs_retard": jobs_retard,
        "total_machines": len(machines),
        "machines_disponibles": machines_dispo,
        "ops_completion_pct": completion,
        "makespan": makespan,
        "taux_retard_pct": taux_retard,
        "unread_alerts": unread_alerts,
        "latest_algo": latest_planning.algorithme if latest_planning else "—",
    })

@app.route("/api/plannings", methods=["GET"])
def get_plannings():
    plannings = Planning.query.order_by(Planning.date_creation.desc()).limit(10).all()
    return jsonify([p.to_dict() for p in plannings])

@app.route("/api/plannings/<int:planning_id>", methods=["GET"])
def get_planning_detail(planning_id):
    planning = Planning.query.get_or_404(planning_id)
    pos = PlanningOperation.query.filter_by(planning_id=planning_id).all()
    return jsonify({
        **planning.to_dict(),
        "operations": [po.to_dict() for po in pos],
    })

@app.route("/api/plannings/<int:planning_id>", methods=["DELETE"])
def delete_planning(planning_id):
    PlanningOperation.query.filter_by(planning_id=planning_id).delete()
    Planning.query.filter_by(id=planning_id).delete()
    db.session.commit()
    return jsonify({"message": "Planning supprimé"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — CONTRAINTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/contraintes", methods=["GET"])
def get_contraintes():
    contraintes = Contrainte.query.all()
    return jsonify([c.to_dict() for c in contraintes])

@app.route("/api/contraintes", methods=["POST"])
def create_contrainte():
    data = request.get_json()
    c = Contrainte(
        type=data["type"],
        valeur=data.get("valeur", ""),
        description=data.get("description", ""),
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@app.route("/api/contraintes/<int:c_id>", methods=["DELETE"])
def delete_contrainte(c_id):
    c = Contrainte.query.get_or_404(c_id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"message": "Contrainte supprimée"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — ALERTES
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/alerts", methods=["GET"])
def get_alerts():
    alerts = get_unread_alerts(db)
    return jsonify(alerts)

@app.route("/api/alerts/all", methods=["GET"])
def get_all_alerts():
    alerts = HistoriqueAlerte.query.order_by(HistoriqueAlerte.date.desc()).limit(50).all()
    return jsonify([a.to_dict() for a in alerts])

@app.route("/api/alerts/<int:alert_id>/read", methods=["POST"])
def read_alert(alert_id):
    mark_alert_read(db, alert_id)
    return jsonify({"message": "Alerte marquée lue"}), 200

@app.route("/api/alerts/read-all", methods=["POST"])
def read_all_alerts():
    HistoriqueAlerte.query.update({"lu": True})
    db.session.commit()
    return jsonify({"message": "Toutes alertes lues"}), 200

# ═══════════════════════════════════════════════════════════════════════════════
# API — IMPORT / EXPORT
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/import-csv", methods=["POST"])
def import_csv():
    if "file" not in request.files:
        return jsonify({"error": "Aucun fichier reçu"}), 400
    file = request.files["file"]
    content = file.read().decode("utf-8-sig")
    result = import_jobs_csv(db, content)
    check_alerts(db)
    return jsonify(result)

@app.route("/api/export/excel", methods=["GET"])
def export_to_excel():
    buf = export_excel(db)
    return send_file(buf, download_name="planning_export.xlsx", as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.route("/api/export/pdf", methods=["GET"])
def export_to_pdf():
    buf = export_pdf_report(db)
    return send_file(buf, download_name="rapport_planning.pdf", as_attachment=True,
                     mimetype="application/pdf")

# ═══════════════════════════════════════════════════════════════════════════════
# API — WHAT-IF SIMULATION
# ═══════════════════════════════════════════════════════════════════════════════

@app.route("/api/whatif", methods=["POST"])
def whatif_simulation():
    """Simulation what-if : recalcul avec modifications temporaires"""
    data = request.get_json()
    algo = data.get("algorithme", "spt").lower()

    # Charger les données actuelles
    jobs = Job.query.filter(Job.statut != "terminé").all()
    machines = Machine.query.filter(Machine.statut == "disponible").all()
    operations = Operation.query.filter(Operation.statut != "terminé").all()

    # Appliquer les modifications temporaires
    mods = data.get("modifications", {})
    for op in operations:
        if str(op.id) in mods.get("durees", {}):
            op.duree = float(mods["durees"][str(op.id)])

    fn = ALGO_MAP.get(algo, run_spt)
    result = fn(jobs, machines, operations)
    kpis = compute_kpis(result["schedule"], jobs, machines)

    return jsonify({
        "makespan": kpis["makespan"],
        "taux_retard": kpis["taux_retard"] * 100,
        "utilisation_machines": kpis["utilisation_machines"],
        "gantt": result["gantt"],
        "note": "Simulation temporaire — aucune modification sauvegardée",
    })

# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)

"""
Système d'alertes automatiques
────────────────────────────────
- Retard : job dépassant sa date_due
- Surcharge : machine avec utilisation > 80 % sur les plannings récents
"""

from datetime import datetime
from database.models import Job, Machine, Planning, PlanningOperation, HistoriqueAlerte


def check_alerts(db):
    """Vérifie et génère des alertes si nécessaire."""
    now = datetime.utcnow()

    # ── 1. Alertes Retard ─────────────────────────────────────────────────────
    jobs_retard = Job.query.filter(
        Job.date_due != None,
        Job.date_due < now,
        Job.statut != "terminé",
    ).all()

    for job in jobs_retard:
        msg = f"⚠️ Retard : Le job « {job.nom} » a dépassé sa date d'échéance ({job.date_due.strftime('%d/%m %H:%M')})."
        existing = HistoriqueAlerte.query.filter(
            HistoriqueAlerte.message.contains(f"job « {job.nom} »"),
            HistoriqueAlerte.type == "retard",
            HistoriqueAlerte.lu == False,
        ).first()
        if not existing:
            db.session.add(HistoriqueAlerte(type="retard", message=msg))

    # ── 2. Alertes Surcharge machines ─────────────────────────────────────────
    latest = Planning.query.order_by(Planning.date_creation.desc()).first()
    if latest:
        pos = PlanningOperation.query.filter_by(planning_id=latest.id).all()
        machine_busy = {}
        for po in pos:
            mid = po.machine_id
            machine_busy[mid] = machine_busy.get(mid, 0) + (po.heure_fin - po.heure_debut)

        makespan = latest.makespan if latest.makespan > 0 else 1
        for machine in Machine.query.all():
            util = machine_busy.get(machine.id, 0) / makespan * 100
            if util > 80:
                msg = f"🔶 Surcharge : La machine « {machine.nom} » est utilisée à {util:.0f}% dans le planning actuel."
                existing = HistoriqueAlerte.query.filter(
                    HistoriqueAlerte.message.contains(f"machine « {machine.nom} »"),
                    HistoriqueAlerte.type == "surcharge",
                    HistoriqueAlerte.lu == False,
                ).first()
                if not existing:
                    db.session.add(HistoriqueAlerte(type="surcharge", message=msg))

    db.session.commit()


def get_unread_alerts(db):
    """Retourne les alertes non lues."""
    alerts = HistoriqueAlerte.query.filter_by(lu=False).order_by(HistoriqueAlerte.date.desc()).all()
    return [a.to_dict() for a in alerts]


def mark_alert_read(db, alert_id):
    """Marque une alerte comme lue."""
    alert = HistoriqueAlerte.query.get(alert_id)
    if alert:
        alert.lu = True
        db.session.commit()

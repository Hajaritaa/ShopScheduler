"""
Données de démonstration — 3 jobs, 3 machines, opérations
Injectées une seule fois au démarrage si la DB est vide.
"""

from datetime import datetime, timedelta
from database.models import Job, Machine, Operation, Contrainte, HistoriqueAlerte


def seed_database(db):
    """Insère les données démo si la base est vide."""
    if Job.query.count() > 0:
        return  # Déjà initialisé

    # ── Machines ──────────────────────────────────────────────────────────────
    m1 = Machine(nom="CNC Alpha", type="CNC", capacite=1, statut="disponible", temps_setup=15)
    m2 = Machine(nom="Robot Soudeur", type="robot", capacite=1, statut="disponible", temps_setup=10)
    m3 = Machine(nom="Poste Assemblage", type="assemblage", capacite=2, statut="disponible", temps_setup=5)
    db.session.add_all([m1, m2, m3])
    db.session.flush()

    # ── Jobs ──────────────────────────────────────────────────────────────────
    now = datetime.utcnow()
    j1 = Job(nom="Pièce Moteur A320", priorite=4,
             date_due=now + timedelta(days=3), statut="en_cours", date_creation=now - timedelta(days=1))
    j2 = Job(nom="Châssis Train d'Atterrissage", priorite=3,
             date_due=now + timedelta(days=5), statut="en_attente", date_creation=now - timedelta(hours=12))
    j3 = Job(nom="Panneau Fuselage B787", priorite=2,
             date_due=now + timedelta(days=7), statut="en_attente", date_creation=now - timedelta(hours=6))
    db.session.add_all([j1, j2, j3])
    db.session.flush()

    # ── Opérations ────────────────────────────────────────────────────────────
    # Job 1 : 3 opérations
    ops = [
        Operation(job_id=j1.id, machine_id=m1.id, duree=45, ordre=1, statut="en_cours"),
        Operation(job_id=j1.id, machine_id=m2.id, duree=30, ordre=2, statut="en_attente"),
        Operation(job_id=j1.id, machine_id=m3.id, duree=20, ordre=3, statut="en_attente"),

        # Job 2 : 3 opérations
        Operation(job_id=j2.id, machine_id=m1.id, duree=60, ordre=1, statut="en_attente"),
        Operation(job_id=j2.id, machine_id=m3.id, duree=25, ordre=2, statut="en_attente"),
        Operation(job_id=j2.id, machine_id=m2.id, duree=35, ordre=3, statut="en_attente"),

        # Job 3 : 3 opérations
        Operation(job_id=j3.id, machine_id=m2.id, duree=50, ordre=1, statut="en_attente"),
        Operation(job_id=j3.id, machine_id=m1.id, duree=40, ordre=2, statut="en_attente"),
        Operation(job_id=j3.id, machine_id=m3.id, duree=30, ordre=3, statut="en_attente"),
    ]
    db.session.add_all(ops)

    # ── Contraintes ───────────────────────────────────────────────────────────
    contraintes = [
        Contrainte(type="délai", valeur="72h", description="Délai maximum de livraison"),
        Contrainte(type="priorité", valeur="4", description="Jobs critiques traités en priorité"),
        Contrainte(type="machine", valeur="CNC Alpha", description="Maintenance planifiée tous les 10 jours"),
    ]
    db.session.add_all(contraintes)

    # ── Alerte initiale ───────────────────────────────────────────────────────
    alerte = HistoriqueAlerte(
        type="info",
        message="Application initialisée avec les données de démonstration (3 jobs, 3 machines, 9 opérations).",
        lu=False,
    )
    db.session.add(alerte)

    db.session.commit()
    print("[OK] Base de donnees initialisee avec les donnees de demonstration.")

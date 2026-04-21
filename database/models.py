"""
Modèles SQLAlchemy — Job Shop Scheduler
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ─── JOBS ────────────────────────────────────────────────────────────────────

class Job(db.Model):
    __tablename__ = "jobs"
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(120), nullable=False)
    priorite      = db.Column(db.Integer, default=2)          # 1=basse 2=normale 3=haute 4=critique
    date_due      = db.Column(db.DateTime, nullable=True)
    statut        = db.Column(db.String(30), default="en_attente")  # en_attente|en_cours|terminé|retard
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    operations = db.relationship("Operation", backref="job", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "priorite": self.priorite,
            "priorite_label": {1: "Basse", 2: "Normale", 3: "Haute", 4: "Critique"}.get(self.priorite, "Normale"),
            "date_due": self.date_due.isoformat() if self.date_due else None,
            "statut": self.statut,
            "date_creation": self.date_creation.isoformat(),
            "nb_operations": len(self.operations),
            "duree_totale": sum(o.duree for o in self.operations),
        }

# ─── MACHINES ────────────────────────────────────────────────────────────────

class Machine(db.Model):
    __tablename__ = "machines"
    id          = db.Column(db.Integer, primary_key=True)
    nom         = db.Column(db.String(120), nullable=False)
    type        = db.Column(db.String(60), default="standard")   # standard|CNC|robot|assemblage
    capacite    = db.Column(db.Integer, default=1)
    statut      = db.Column(db.String(30), default="disponible")  # disponible|occupée|maintenance
    temps_setup = db.Column(db.Float, default=0.0)               # minutes

    operations = db.relationship("Operation", backref="machine", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "type": self.type,
            "capacite": self.capacite,
            "statut": self.statut,
            "temps_setup": self.temps_setup,
        }

# ─── OPERATIONS ──────────────────────────────────────────────────────────────

class Operation(db.Model):
    __tablename__ = "operations"
    id          = db.Column(db.Integer, primary_key=True)
    job_id      = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    machine_id  = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=False)
    duree       = db.Column(db.Float, nullable=False)  # minutes
    ordre       = db.Column(db.Integer, default=1)
    statut      = db.Column(db.String(30), default="en_attente")
    heure_debut = db.Column(db.DateTime, nullable=True)
    heure_fin   = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_nom": self.job.nom if self.job else "—",
            "machine_id": self.machine_id,
            "machine_nom": self.machine.nom if self.machine else "—",
            "duree": self.duree,
            "ordre": self.ordre,
            "statut": self.statut,
            "heure_debut": self.heure_debut.isoformat() if self.heure_debut else None,
            "heure_fin": self.heure_fin.isoformat() if self.heure_fin else None,
        }

# ─── PLANNINGS ───────────────────────────────────────────────────────────────

class Planning(db.Model):
    __tablename__ = "plannings"
    id            = db.Column(db.Integer, primary_key=True)
    nom           = db.Column(db.String(200), nullable=False)
    algorithme    = db.Column(db.String(30), nullable=False)  # SPT|LPT|EDD|GENETIC
    makespan      = db.Column(db.Float, default=0.0)
    taux_retard   = db.Column(db.Float, default=0.0)          # 0.0–1.0
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)

    operations_planifiees = db.relationship("PlanningOperation", backref="planning", lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "nom": self.nom,
            "algorithme": self.algorithme,
            "makespan": self.makespan,
            "taux_retard": round(self.taux_retard * 100, 1),
            "date_creation": self.date_creation.isoformat(),
        }

# ─── PLANNING_OPERATIONS ─────────────────────────────────────────────────────

class PlanningOperation(db.Model):
    __tablename__ = "planning_operations"
    id           = db.Column(db.Integer, primary_key=True)
    planning_id  = db.Column(db.Integer, db.ForeignKey("plannings.id"), nullable=False)
    operation_id = db.Column(db.Integer, db.ForeignKey("operations.id"), nullable=True)
    heure_debut  = db.Column(db.Float, nullable=False)   # offset en minutes depuis t=0
    heure_fin    = db.Column(db.Float, nullable=False)
    machine_id   = db.Column(db.Integer, db.ForeignKey("machines.id"), nullable=True)

    def to_dict(self):
        op = Operation.query.get(self.operation_id) if self.operation_id else None
        machine = Machine.query.get(self.machine_id) if self.machine_id else None
        return {
            "id": self.id,
            "planning_id": self.planning_id,
            "operation_id": self.operation_id,
            "job_nom": op.job.nom if op and op.job else "—",
            "machine_nom": machine.nom if machine else "—",
            "heure_debut": self.heure_debut,
            "heure_fin": self.heure_fin,
            "machine_id": self.machine_id,
        }

# ─── CONTRAINTES ─────────────────────────────────────────────────────────────

class Contrainte(db.Model):
    __tablename__ = "contraintes"
    id          = db.Column(db.Integer, primary_key=True)
    type        = db.Column(db.String(60), nullable=False)   # priorité|délai|machine|autre
    valeur      = db.Column(db.String(200), default="")
    description = db.Column(db.Text, default="")

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "valeur": self.valeur,
            "description": self.description,
        }

# ─── HISTORIQUE_ALERTES ───────────────────────────────────────────────────────

class HistoriqueAlerte(db.Model):
    __tablename__ = "historique_alertes"
    id      = db.Column(db.Integer, primary_key=True)
    type    = db.Column(db.String(30), nullable=False)   # retard|surcharge|maintenance|info
    message = db.Column(db.Text, nullable=False)
    date    = db.Column(db.DateTime, default=datetime.utcnow)
    lu      = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "message": self.message,
            "date": self.date.isoformat(),
            "lu": self.lu,
        }

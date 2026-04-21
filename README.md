# Job Shop Scheduler — MES v3.0

Application web **Flask** complète de gestion et d'ordonnancement de production (Job Shop Scheduling).

---

## 🚀 Lancement rapide

```bash
# 1. Créer l'environnement virtuel
python -m venv venv
.\venv\Scripts\activate        # Windows
# source venv/bin/activate     # Linux/Mac

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
python app.py
```

L'application démarre sur **http://localhost:8000**

---

## 📁 Structure du projet

```
ord projet/
├── app.py                        # Point d'entrée Flask + toutes les routes API
├── requirements.txt
├── README.md
├── database/
│   ├── models.py                 # Modèles SQLAlchemy
│   └── seed.py                   # Données de démonstration
├── backend/
│   ├── scheduler.py              # Algorithmes SPT, LPT, EDD, Génétique
│   ├── kpis.py                   # Calcul KPIs temps réel
│   ├── alerts.py                 # Système d'alertes automatiques
│   └── import_export.py          # Import CSV / Export Excel + PDF
└── frontend/
    ├── static/
    │   ├── css/main.css          # Thème professionnel clair complet
    │   └── js/
    │       ├── app.js            # Navigation SPA, KPIs, alertes
    │       ├── crud.js           # CRUD Jobs / Machines / Opérations
    │       ├── gantt_view.js     # Gantt interactif (frappe-gantt + canvas)
    │       ├── charts.js         # Chart.js : doughnut, bar, radar
    │       └── whatif.js         # Simulation What-If
    └── templates/
        └── index.html            # SPA shell unique
```

---

## 🗄 Base de données

SQLite avec SQLAlchemy — fichier `database/scheduler.db`

| Table | Description |
|-------|-------------|
| `jobs` | Ordres de fabrication |
| `machines` | Parc machines |
| `operations` | Séquences opératoires |
| `plannings` | Plannings générés |
| `planning_operations` | Détail des plannings |
| `contraintes` | Règles métier |
| `historique_alertes` | Journal des alertes |

**Données de démo** injectées automatiquement au premier démarrage :
- 3 jobs aéronautiques (Pièce Moteur A320, Châssis Train d'Atterrissage, Panneau Fuselage)
- 3 machines (CNC Alpha, Robot Soudeur, Poste Assemblage)
- 9 opérations (3 par job)

---

## 🧬 Algorithmes d'ordonnancement

| Algo | Description |
|------|-------------|
| **SPT** | Shortest Processing Time — plus court en premier |
| **LPT** | Longest Processing Time — plus long en premier |
| **EDD** | Earliest Due Date — date d'échéance la plus proche |
| **Génétique** | Algorithme évolutif (crossover OX, mutation, élitisme) |

---

## 📡 API REST

| Méthode | Route | Description |
|---------|-------|-------------|
| GET/POST | `/api/jobs` | Liste et création de jobs |
| GET/PUT/DELETE | `/api/jobs/<id>` | CRUD job |
| GET/POST | `/api/machines` | Liste et création machines |
| GET/PUT/DELETE | `/api/machines/<id>` | CRUD machine |
| GET/POST | `/api/operations` | Liste et création opérations |
| POST | `/api/schedule` | Lancer ordonnancement |
| POST | `/api/compare` | Comparer les 4 algorithmes |
| GET | `/api/kpis` | KPIs temps réel |
| GET | `/api/plannings` | Historique plannings |
| POST | `/api/whatif` | Simulation What-If |
| POST | `/api/import-csv` | Import CSV jobs |
| GET | `/api/export/excel` | Export Excel |
| GET | `/api/export/pdf` | Export PDF |
| GET | `/api/alerts/all` | Toutes les alertes |

---

## 🎨 Design

- **Thème** : Professionnel clair (#F8F9FC)
- **Accent** : Bleu corporate #2563EB + Violet #7C3AED
- **Police** : Inter (Google Fonts)
- **Composants** : Sidebar 240px fixe, KPI cards avec top-border coloré, tableaux alternés, badges pastel, transitions 150ms

---

## 📦 Dépendances clés

- `flask` — Framework web
- `flask-sqlalchemy` — ORM base de données
- `openpyxl` — Export Excel
- `reportlab` — Export PDF
- `frappe-gantt` (CDN) — Diagramme Gantt interactif
- `chart.js` (CDN) — Graphiques KPI et comparaison

---

## 📄 Format CSV d'import

```csv
nom,priorite,date_due,statut
Pièce Turbine X,3,2026-05-15,en_attente
Rotor Moteur Y,4,2026-05-10,en_attente
Panneau Composite Z,2,2026-06-01,en_attente
```

Formats de date acceptés : `YYYY-MM-DD`, `DD/MM/YYYY`, `YYYY-MM-DDTHH:MM`

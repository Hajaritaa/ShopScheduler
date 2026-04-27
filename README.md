# ShopScheduler

## Description
Application Django d'ordonnancement industriel - Flow Shop, Job Shop, Machines Parallèles. Permet de gérer des jobs, machines, opérations et de visualiser le planning via un diagramme de Gantt interactif.

## Fonctionnalités
- Tableau de bord avec KPIs
- Gestion des Jobs, Machines, Opérations
- Algorithmes d'ordonnancement : SPT, LPT, EDD, FIFO, LIFO, SIFO, JOHNSON
- Diagramme de Gantt interactif (Plotly)
- Carte de l'atelier 2D
- Comparaison des algorithmes
- Suivi des contraintes et statuts

## Prérequis
- Python 3.10+
- Git

## Installation et lancement

### 1. Cloner le projet
```bash
git clone https://github.com/Hajaritaa/ShopScheduler.git
cd ShopScheduler
```

### 2. Installer les dépendances
```bash
pip install django django-crispy-forms crispy-bootstrap5 plotly pandas
```

### 3. Initialiser la base de données
```bash
python manage.py migrate
```

### 4. Créer un compte administrateur
```bash
python manage.py createsuperuser
```

### 5. Lancer le serveur
```bash
python manage.py runserver
```

### 6. Ouvrir l'application
Ouvrez votre navigateur et allez sur : http://127.0.0.1:8000/

## Pages disponibles
| Page | URL |
|---|---|
| Tableau de bord | http://127.0.0.1:8000/ |
| Jobs | http://127.0.0.1:8000/jobs/ |
| Machines | http://127.0.0.1:8000/machines/ |
| Gantt | http://127.0.0.1:8000/gantt/ |
| Comparer Algos | http://127.0.0.1:8000/compare/ |
| Carte Atelier | http://127.0.0.1:8000/workshop/ |
| Contraintes | http://127.0.0.1:8000/constraints/ |
| Admin | http://127.0.0.1:8000/admin/ |

## Technologies
- Django 5.2
- Plotly
- SQLite
- Bootstrap 5
- crispy-forms

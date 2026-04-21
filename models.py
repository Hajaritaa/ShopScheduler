from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Machine(models.Model):
    TYPE_CHOICES = [
        ('job_shop', 'Job Shop'),
        ('flow_shop', 'Flow Shop'),
        ('parallele', 'Machines Parallèles'),
    ]
    nom = models.CharField(max_length=100)
    type_atelier = models.CharField(max_length=20, choices=TYPE_CHOICES, default='job_shop')
    capacite = models.IntegerField(default=1)
    disponible_depuis = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.nom} ({self.get_type_atelier_display()})"

class Job(models.Model):
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
    ]
    nom = models.CharField(max_length=100)
    date_arrivee = models.DateTimeField()
    due_date = models.DateTimeField()
    priorite = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=3)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')

    def __str__(self):
        return self.nom

class Operation(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='operations')
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, related_name='operations')
    ordre = models.IntegerField(default=1)
    duree_preparation = models.IntegerField(help_text="Durée de préparation en minutes")
    duree_execution = models.IntegerField(help_text="Durée d'exécution en minutes")
    
    # Scheduled times
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.job.nom} - Op {self.ordre} ({self.machine.nom})"

    class Meta:
        ordering = ['ordre']

class Contrainte(models.Model):
    TYPE_CHOICES = [
        ('precedence', 'Précédence'),
        ('exclusion', 'Exclusion'),
        ('time_window', 'Fenêtre de temps'),
    ]
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    job_source = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='contraintes_sources')
    job_cible = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='contraintes_cibles', null=True, blank=True)
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, null=True, blank=True)
    valeur = models.IntegerField(help_text="Valeur de contrainte (min ou autre)", null=True, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"Contrainte {self.get_type_display()} - {self.description}"

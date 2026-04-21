from django import forms
from .models import Machine, Job, Operation, Contrainte

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['nom', 'date_arrivee', 'due_date', 'priorite', 'statut']
        widgets = {
            'date_arrivee': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class MachineForm(forms.ModelForm):
    class Meta:
        model = Machine
        fields = ['nom', 'type_atelier', 'capacite', 'disponible_depuis']
        widgets = {
            'disponible_depuis': forms.DateTimeInput(attrs={'type': 'datetime-local', 'required': False}),
        }

class OperationForm(forms.ModelForm):
    class Meta:
        model = Operation
        fields = ['machine', 'ordre', 'duree_preparation', 'duree_execution']

class ContrainteForm(forms.ModelForm):
    class Meta:
        model = Contrainte
        fields = ['type', 'job_source', 'job_cible', 'machine', 'valeur', 'description']

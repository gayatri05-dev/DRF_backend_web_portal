from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.models import PermissionsMixin


# Create your models here.
class Patient(AbstractUser):
    fullName = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    dob = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    address = models.TextField(null=True, blank=True)
    role = models.CharField(max_length=50, choices=(('Admin', 'admin'), ('doctor', 'Doctor'),('patient','Patient')))

    # Overriding username as optional
    USERNAME_FIELD = 'email'  # Login with email
    REQUIRED_FIELDS = ['username', 'fullName', 'password'] 


class Doctor(models.Model):
    user = models.OneToOneField(Patient, on_delete=models.CASCADE)  # Link to the Patient model
    specialization = models.CharField(max_length=255)
    qualification = models.CharField(max_length=255)
    years_of_experience = models.IntegerField()
    license_number = models.CharField(max_length=255)
    registration_number = models.CharField(max_length=255)
    consultation_fee = models.DecimalField(max_digits=6, decimal_places=2)
    available_days = models.JSONField()  # e.g., ["Monday", "Wednesday", "Friday"]
    available_hours = models.JSONField()  # e.g., ["9:00 AM - 5:00 PM"]
    max_appointments_per_day = models.IntegerField()
    location = models.CharField(max_length=255)


    def __str__(self):
        return f"{self.user.fullName} - {self.specialization}"


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE)
    
    appointment_date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    
    disease = models.CharField(max_length=255, blank=True, null=True)  # Disease patient is suffering from
    visit_reason = models.TextField(blank=True, null=True)  # Reason for the visit
    symptoms = models.TextField(blank=True, null=True)  # Symptoms described by the patient

    def __str__(self):
        return f"Appointment {self.id} with Dr. {self.doctor.specialization} on {self.appointment_date}"



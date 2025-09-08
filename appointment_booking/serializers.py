from rest_framework import serializers
from django.contrib.auth.hashers import make_password
from .models import Patient ,Doctor,Appointment
from django.contrib.auth import get_user_model
import secrets
import string
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError


class RegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['username', 'fullName', 'email', 'dob', 'phone_number', 'password', 'address', 'role']
        extra_kwargs = {
            'password': {'write_only': True}  # Prevent password from being displayed in responses
        }

    def create(self, validated_data):
        # Hash the password before saving
        validated_data['password'] = make_password(validated_data['password'])
        return super().create(validated_data)

class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['username', 'fullName', 'dob', 'phone_number', 'address',  'role']

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'username', 'fullName', 'email', 'dob', 'phone_number', 'address', 'role', 'password']
        read_only_fields = ['id', 'email']  # Prevent updating email and ID
        extra_kwargs = {
            'password': {'write_only': True},  # Password should not be readable in responses
        }

    def update(self, instance, validated_data):
        # Handle password hashing
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
        return super().update(instance, validated_data)

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['id', 'username', 'fullName', 'email', 'dob', 'phone_number', 'address', 'role']

    def update(self, instance, validated_data):
        # Update user fields except for password
        instance.fullName = validated_data.get('fullName', instance.fullName)
        instance.email = validated_data.get('email', instance.email)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)
        instance.address = validated_data.get('address', instance.address)
        instance.role = validated_data.get('role', instance.role)

        instance.save()
        return instance        
    
class UserSSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'password']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['fullName', 'email', 'dob', 'phone_number', 'address', 'role', 'username', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'role': {'default': 'doctor'}  # Default role is "Doctor" for this API
        }

    def create(self, validated_data):
        # Create the Patient (Doctor user) with a hashed password
        password = validated_data.pop('password')
        user = Patient.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class DoctorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = [
            'user','specialization', 'qualification', 'years_of_experience', 'license_number',
            'registration_number', 'consultation_fee', 'available_days',
            'available_hours', 'max_appointments_per_day', 'location','id'

        ]

class DoctorSerializers(serializers.ModelSerializer):
    class Meta:
        model = Doctor  # Assuming the Doctor model exists
        fields = [
            'specialization', 
            'qualification', 
            'years_of_experience', 
            'license_number', 
            'registration_number', 
            'consultation_fee', 
            'available_days', 
            'available_hours', 
            'max_appointments_per_day', 
            'location'
        ]

class AddDoctorSerializer(serializers.Serializer):
    user = UserSerializer()  # Add user field here, as UserSerializer is used for user data
    doctor = DoctorSerializers()  # Define the doctor field as well

    class Meta:
        fields = ['user', 'doctor']  

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        doctor_data = validated_data.pop('doctor')

        user = Patient.objects.create_user(**user_data)  # Assuming this is how you're creating the user
        doctor = Doctor.objects.create(user=user, **doctor_data)  # Associate the doctor with the user

        return {"user": user, "doctor": doctor}

class GetDoctorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient  # Replace with your actual user model
        fields = ['username', 'fullName', 'email', 'phone_number']  # Adjust fields as needed

class DoctorSerializer(serializers.ModelSerializer):
    # Add the UserSerializer as a nested serializer to include personal details
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = [
            'id',
            'user',  # This will include the doctor's personal details from the User model
            'specialization',
            'qualification',
            'years_of_experience',
            'license_number',
            'registration_number',
            'consultation_fee',
            'available_days',
            'available_hours',
            'max_appointments_per_day',
            'location'
        ]

class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['id', 'patient', 'doctor', 'appointment_date', 'status','disease','visit_reason','symptoms']
        
    def validate(self, data):
        appointment_date = data.get('appointment_date')
        if appointment_date <= timezone.now():
            raise serializers.ValidationError("Appointment date must be in the future.")
        return data

class GetAppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'

class AppointmentConfirmationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ['confirmation_status']
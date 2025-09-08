from rest_framework import status,permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import PatientSerializer
from rest_framework_simplejwt.tokens import AccessToken,RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail 
from .emails import send_notification_email , send_appointment_email
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import Patient,Doctor,Appointment
from .serializers import RegistrationSerializer,UserProfileSerializer,UserProfileUpdateSerializer,AddDoctorSerializer,DoctorSerializer,AppointmentSerializer,GetAppointmentSerializer
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import make_aware
from datetime import datetime
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils.dateparse import parse_datetime
import logging
logger = logging.getLogger(__name__)

class PatientRegisterView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()

            send_notification_email(user.email, 'Register', {'user': user})

            return Response({'message': 'User Created Successfully'}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginUserView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        # Authenticate the user
        user = authenticate(request, email=email, password=password)

        if user is not None:
            access = AccessToken.for_user(user)
            refresh = RefreshToken.for_user(user)

            # Send notification email (optional)
            send_notification_email(user.email, 'Login', {'user': user})

            # Prepare the response data based on user type
            response_data = {
                'message': 'Login successful!',
                'access_token': str(access),
                'refresh_token': str(refresh),
                'role': user.role,
                'id': user.id,
                'fullName': user.fullName,
                'email': user.email,
                'dob': user.dob,
                'phone_number': user.phone_number,
                'address': user.address,
                'is_superuser':user.is_superuser
              
            }

            # Check if the user is a superuser
            if user.is_superuser is True:
                response_data['message'] = 'Superadmin login successful!'
            
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    def post(self, request):
        return Response({'message': 'Logout successful. Please delete your access token on the client side.'}, status=status.HTTP_205_RESET_CONTENT)
    
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]  # Require authentication

    def get(self, request, id):
        try:
            # Fetch the user by ID
            user = Patient.objects.get(id=id)
            # Serialize the user data
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Patient.DoesNotExist:
            # Return 404 if user not found
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
class UserProfileUpdateView(APIView):
    # permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get_object(self, user_id):
        try:
            return Patient.objects.get(id=user_id)
        except Patient.DoesNotExist:
            return None
    
    def put(self, request, id):
        user = self.get_object(id)
        # if not user:
        #     return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # if user != request.user:
        #     return Response({"error": "You do not have permission to update this profile"}, status=status.HTTP_403_FORBIDDEN)

        # Extract password and confirm password fields from the request data
        password = request.data.get("password", None)
        current_password = request.data.get("current_password", None)
        
        if password and current_password:
            if not user.check_password(current_password):
                return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(password)
            user.save()

        request.data.pop("password", None)
        request.data.pop("current_password", None)

        # Update user profile data (excluding password fields)
        serializer = UserProfileUpdateSerializer(user, data=request.data)
        
        if serializer.is_valid():
            serializer.save()  # Save the updated user data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, id):
        # Similar to `put`, but allows partial updates.
        user = self.get_object(id)
        if not user:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        if user != request.user:
            return Response({"error": "You do not have permission to update this profile"}, status=status.HTTP_403_FORBIDDEN)

        # Extract password and confirm password fields from the request data
        password = request.data.get("password", None)
        current_password = request.data.get("current_password", None)
        
        if password and current_password:
            # Check if the current password is correct
            if not user.check_password(current_password):
                return Response({"error": "Current password is incorrect"}, status=status.HTTP_400_BAD_REQUEST)
            # Set the new password securely
            user.set_password(password)
            user.save()

        # Remove password from the request data to avoid overwriting with blank value
        request.data.pop("password", None)
        request.data.pop("current_password", None)

        # Update user profile data (excluding password fields)
        serializer = UserProfileSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Save the updated user data
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
        
class AddDoctorView(APIView):
   
    def post(self, request, *args, **kwargs):
        serializer = AddDoctorSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            return Response({
                "message": "Doctor added successfully!",
                "user": {
                    "fullName": result["user"].fullName,
                    "email": result["user"].email,
                    "username": result["user"].username,
                    "role": result["user"].role  
                },
                "doctor": {
                    "specialization": result["doctor"].specialization,
                    "qualification": result["doctor"].qualification,
                    "location": result["doctor"].location
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DoctorListView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request):
        # Get query parameters
        specialization = request.query_params.get('specialization', None)
        location = request.query_params.get('location', None)
        ordering = request.query_params.get('ordering', None)

        # Filter doctors based on the linked user's role
        doctors = Doctor.objects.filter(user__role='doctor')  # Assuming the related user model has a 'role' field

        if specialization:
            doctors = doctors.filter(specialization__icontains=specialization)
        if location:
            doctors = doctors.filter(location__icontains=location)

        # Sorting logic (if provided)
        if ordering:
            if ordering in ['specialization', 'location', 'consultation_fee']:
                doctors = doctors.order_by(ordering)

        # Serialize and return the response
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class BookAppointmentView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request, doctor_id):
        logger.debug(f"Received request with token: {request.headers.get('Authorization')}")
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate patient is not booking an appointment with themselves
        if request.user.role != 'patient':
            return Response({"detail": "Only patients can book appointments."}, status=status.HTTP_400_BAD_REQUEST)

        # Extract the appointment data from the request
        appointment_date = request.data.get('appointment_date')
        disease = request.data.get('disease')
        visit_reason = request.data.get('visit_reason')
        symptoms = request.data.get('symptoms')

        # Parse the appointment_date into a datetime object
        appointment_date = parse_datetime(appointment_date)

        # Check if the date is a valid datetime object
        if not appointment_date:
            return Response({"detail": "Invalid appointment date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Make appointment_date aware if it's naive
        if appointment_date.tzinfo is None:
            appointment_date = timezone.make_aware(appointment_date, timezone.get_current_timezone())

        # Validate appointment date is in the future
        if appointment_date <= timezone.now():
            return Response({"detail": "Appointment date must be in the future."}, status=status.HTTP_400_BAD_REQUEST)

        # Create the appointment
        appointment = Appointment.objects.create(
            patient=request.user,
            doctor=doctor,
            appointment_date=appointment_date,
            disease=disease,
            visit_reason=visit_reason,
            symptoms=symptoms
        )

        # Send email to the patient
        try:
            send_appointment_email(request.user.email,appointment)
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return Response({"detail": "Appointment booked, but email notification failed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Serialize the appointment data and return response
        serializer = AppointmentSerializer(appointment)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

class AppointmentListForDoctorView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        if request.user.role != 'doctor':
            return Response({"detail": "You are not authorized to view appointments."}, status=status.HTTP_403_FORBIDDEN)

        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response({"detail": "Doctor profile not found."}, status=status.HTTP_404_NOT_FOUND)
        
        appointments = Appointment.objects.filter(doctor=doctor)
        
        if not appointments.exists():
            return Response({"detail": "No appointments found for this doctor."}, status=status.HTTP_404_NOT_FOUND)

        serializer = GetAppointmentSerializer(appointments, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

class DoctorDetailView(APIView):
    def get(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(id=doctor_id)
        except Doctor.DoesNotExist:
            return Response({"detail": "Doctor not found."}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = DoctorSerializer(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)

logger = logging.getLogger(__name__)

class RescheduleAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, appointment_id):
        
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the authenticated user is the one who booked the appointment
        if appointment.patient != request.user:
            return Response({"detail": "You can only view your own appointments."}, status=status.HTTP_403_FORBIDDEN)

        # Serialize the appointment and return it
        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data)

    # Step 2: Update the appointment (POST)
    def post(self, request, appointment_id):
        """
        Allows a patient to reschedule their appointment by providing a new date.
        """
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"detail": "Appointment not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the user is the one who booked this appointment
        if appointment.patient != request.user:
            return Response({"detail": "You can only reschedule your own appointments."}, status=status.HTTP_403_FORBIDDEN)

        # Extract the new appointment date from the request
        new_appointment_date_str = request.data.get('appointment_date')
        if not new_appointment_date_str:
            return Response({"detail": "New appointment date is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Convert the string to a datetime object
        new_appointment_date = parse_datetime(new_appointment_date_str)

        # Debugging: Check if the datetime was parsed correctly
        if not new_appointment_date:
            logger.error(f"Invalid appointment date: {new_appointment_date_str}")
            return Response({"detail": "Invalid appointment date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Make it timezone-aware if it's naive
        if new_appointment_date.tzinfo is None:
            new_appointment_date = timezone.make_aware(new_appointment_date)

        # Validate that the new appointment date is in the future
        if new_appointment_date <= timezone.now():
            return Response({"detail": "Appointment date must be in the future."}, status=status.HTTP_400_BAD_REQUEST)

        # Extract other fields (disease, visit_reason, symptoms) from the request
        disease = request.data.get('disease')
        visit_reason = request.data.get('visit_reason')
        symptoms = request.data.get('symptoms')

        # Update the appointment with the new date and other details
        appointment.appointment_date = new_appointment_date
        
        if disease:
            appointment.disease = disease
        if visit_reason:
            appointment.visit_reason = visit_reason
        if symptoms:
            appointment.symptoms = symptoms

        appointment.save()

        logger.debug(f"Appointment {appointment.id} updated with new details: "
                     f"date={appointment.appointment_date}, disease={appointment.disease}, "
                     f"visit_reason={appointment.visit_reason}, symptoms={appointment.symptoms}")

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)

class GetAppointmentsView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        """
        Fetch all appointments booked by the authenticated user.
        """
        appointments = Appointment.objects.filter(patient=request.user)

        if not appointments.exists():
            return Response({"detail": "No appointments found for this user."}, status=status.HTTP_404_NOT_FOUND)

        serializer = AppointmentSerializer(appointments, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class DoctorAppointmentsView(APIView):
    """
    View to retrieve appointments specific to the logged-in doctor.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            doctor = Doctor.objects.get(user=request.user)

            appointments = Appointment.objects.filter(doctor=doctor)

            serializer = AppointmentSerializer(appointments, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Doctor.DoesNotExist:
            return Response(
                {"error": "Doctor profile not found for the logged-in user."},
                status=status.HTTP_404_NOT_FOUND
            )
        
class ConfirmAppointmentView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"error": "Appointment not found"}, status=status.HTTP_404_NOT_FOUND)

        if request.user.role != 'doctor':
            return Response({"error": "You do not have permission to confirm this appointment"}, status=status.HTTP_403_FORBIDDEN)


        appointment.status = 'Confirmed'
        appointment.save()

        serializer = AppointmentSerializer(appointment)
        return Response(serializer.data, status=status.HTTP_200_OK)
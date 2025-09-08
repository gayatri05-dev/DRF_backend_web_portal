from django.urls import path 
from . import views 
from rest_framework_simplejwt import views as jwt_views

urlpatterns = [
    path('patient-register',views.PatientRegisterView.as_view(),name='register'),
    path('login',views.LoginUserView.as_view(),name="login"),
    path('token/', jwt_views.TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/logout/',views.LogoutView.as_view(),name="logout"),
    path('api/get-profile',views.UserProfileView.as_view(),name='profile'),
    path('api/get-user',views.UserProfileView.as_view(),name="get"),
    path('get-by-id/<int:id>/',views.UserProfileView.as_view(),name="id"),
    path('user-update/<int:id>/',views.UserProfileUpdateView.as_view(), name='update-user-profile'),
    path('add-doctor/', views.AddDoctorView.as_view(), name='add-doctor'),
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('appointments/book/<int:doctor_id>/', views.BookAppointmentView.as_view(), name='book_appointment'),
    path('get-appointments/patient/', views.AppointmentListForDoctorView.as_view(), name='appointments-by-doctor'),
    path('doctor/<int:doctor_id>/', views.DoctorDetailView.as_view(), name='doctor_detail'),
    path('appointments/reschedule/<int:appointment_id>/', views.RescheduleAppointmentView.as_view(), name='get_appointment'),
    path('appointments/reschedule/<int:appointment_id>/update/', views.RescheduleAppointmentView.as_view(), name='reschedule_appointment'),
    path('appointments/by-user', views.GetAppointmentsView.as_view(), name='get-appointments'),
    path('appointments/doctor/<int:doctor_id>/',views.DoctorAppointmentsView.as_view(), name='appointment-list'),
    path('appointments/confirm/<int:appointment_id>/', views.ConfirmAppointmentView.as_view(), name='confirm-appointment'),
]
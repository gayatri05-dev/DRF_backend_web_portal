from django.core.mail import send_mail
from django.utils.html import strip_tags

def send_notification_email(email,notification_type, context=None):
    subject = ''
    html_message = ''
    
    if notification_type == 'Register':
        subject = 'User Registered Successfully!'
    elif notification_type == 'Login':
        subject = 'User Login Successfully!' 
    elif notification_type == 'account_verification':
        subject = 'Verify Your Account'
        
    plain_message = strip_tags(html_message)  # Strip HTML tags for plain text version

    send_mail(
        subject,
        plain_message,
        'gayakishorkhairkar@gmail.com',  # Use your default from email
        [email],
        html_message=html_message,
        fail_silently=False,
    )


from django.core.mail import send_mail
from django.utils.html import strip_tags

def send_appointment_email(email, appointment):
    """
    Sends an appointment booking confirmation email to the patient.
    
    :param email: Recipient's email address
    :param appointment: The appointment object containing appointment details
    """
    subject = 'Appointment Booking Confirmation'
    
    # Access appointment attributes directly
    patient_name = appointment.patient.fullName # Assuming the patient is related to a user with a full name
    appointment_date = appointment.appointment_date.strftime('%Y-%m-%d %H:%M')  # Format the date as needed

    # Simple HTML message
    html_message = f"""
    <html>
        <body>
            <h2>Appointment Booking Confirmation</h2>
            <p>Dear {patient_name},</p>
            <p>Your appointment has been successfully booked for {appointment_date}.</p>
            <p>Thank you,</p>
            <p>Your Clinic Team</p>
        </body>
    </html>
    """
    
    # Create a plain text version of the email
    plain_message = strip_tags(html_message)

    # Send the email
    send_mail(
        subject,
        plain_message,
        'gayakishorkhairkar@gmail.com',  # Replace with your default sender email
        [email],
        html_message=html_message,
        fail_silently=False,
    )

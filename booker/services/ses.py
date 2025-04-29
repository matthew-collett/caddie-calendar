import boto3


def send_email(config, subject, body):
    client = boto3.client('ses', region_name=config.region)
    client.send_email(
        Source=config.sender_email,
        Destination={
            'ToAddresses': [
                config.email
            ]
        },
        Message={
            'Subject': {
                'Data': subject,
                'Charset': 'UTF-8'
            },
            'Body': {
                'Text': {
                    'Data': body,
                    'Charset': 'UTF-8'
                }
            }
        }
    )


def success_email(config, booking_details):
    subject = "Caddie Calendar - Booking Successful!"
    body = (f"Hi Jeff & Sonia,\n\n"
            f"Great news! We've successfully booked your tee time for {config.date} at {booking_details['time']}. "
            f"Your booking ID is {booking_details['bookingId']}.\n\n"
            f"Enjoy your game!\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)


def login_failed_email(config):
    subject = "Caddie Calendar - Login Failed"
    body = (f"Hi Jeff & Sonia,\n\n"
            f"We were unable to log in to book your tee time for {config.date}. "
            f"Please contact your amazing and beloved son for help with this issue.\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)


def no_bookings_email(config):
    subject = "Caddie Calendar - No Bookings Found"
    body = (f"Hi Jeff & Sonia,\n\n"
            f"We were unable to find any available tee times for {config.date}. "
            f"Please manually log in to book your tee time as soon as possible.\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)


def no_desired_bookings_email(config):
    subject = "Caddie Calendar - No Desired Bookings Found"
    body = (f"Hi Jeff & Sonia,\n\n"
            f"We were unable to find any available tee times for {config.date} at {config.time.strftime('%H:%M')} within +/- 30 minutes. "
            f"Please manually log in to book your tee time as soon as possible.\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)


def failed_attempts_email(config, errors):
    subject = "Caddie Calendar - All Booking Attempts Failed"
    attempts = "\n".join([f"{i+1}. {error}" for i, error in enumerate(errors)])
    body = (f"Hi Jeff & Sonia,\n\n"
            f"We were unable to book a tee time after trying {len(errors)} times within your desired interval. "
            f"Booking attempts summary:\n\n{attempts}\n\n"
            f"Please manually log in to book your tee time as soon as possible.\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)


def error_email(config, error):
    subject = "Caddie Calendar - Booking Error"
    body = (f"Hi Jeff & Sonia,\n\n"
            f"An error occurred during the booking process for {config.date}:\n\n{error}\n\n"
            f"Please contact your amazing and beloved son for help with this issue.\n\n"
            f"Regards,\nCaddie Calendar")
    send_email(config, subject, body)

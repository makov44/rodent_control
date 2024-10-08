import json
import boto3
import logging
import base64
from urllib.parse import parse_qs

# Set up logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the SES client
ses_client = boto3.client('ses')

# Set both sender and recipient emails to your email address
SENDER_EMAIL = "makov.sergey@gmail.com"  # Must be verified in AWS SES
RECIPIENT_EMAIL = "makov.sergey@gmail.com"  # Your email address

def lambda_handler(event, context):
    # Log the full event
    logger.info(f"Received event: {json.dumps(event)}")

    # Parse the input from the event
    try:
        if event.get('isBase64Encoded', False):
            body = base64.b64decode(event['body']).decode('utf-8')
            logger.info(f"Decoded body: {body}")
            # Parse the form data
            form_data = parse_qs(body)
        else:
            body = event['body']
            if isinstance(body, str):
                form_data = parse_qs(body)
            else:
                form_data = body

        # Extract single values from the parsed form data
        name = form_data.get('name', ['Guest'])[0]
        user_email = form_data.get('userEmail', ['no-reply@example.com'])[0]
        phone_number = form_data.get('phoneNumber', ['Not provided'])[0]
        zipcode = form_data.get('zipcode', ['Not provided'])[0]
        project_type = form_data.get('projectType', ['Not provided'])[0]
        property_type = form_data.get('propertyType', ['Not provided'])[0]
        message_content = form_data.get('message', ['No message provided.'])[0]

    except Exception as e:
        logger.error(f"Error parsing event body: {str(e)}")
        return {
            'statusCode': 400,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Required for CORS support
            },
            'body': json.dumps({
                'message': 'Invalid input data. Please check your submission.'
            })
        }
    
    # Log the parsed data
    logger.info(f"Parsed data - Name: {name}, Email: {user_email}, Phone: {phone_number}, Zipcode: {zipcode}, Project Type: {project_type}, Property Type: {property_type}, Message: {message_content}")

    # Prepare the email content
    subject = 'New Form Submission'
    body_text = f"""You have received a new form submission.

Name: {name}
Email: {user_email}
Phone Number: {phone_number}
Zipcode: {zipcode}
Project Type: {project_type}
Property Type: {property_type}
Message:
{message_content}
"""
    body_html = f"""
    <html>
    <head></head>
    <body>
      <h1>New Form Submission</h1>
      <p><strong>Name:</strong> {name}</p>
      <p><strong>Email:</strong> {user_email}</p>
      <p><strong>Phone Number:</strong> {phone_number}</p>
      <p><strong>Zipcode:</strong> {zipcode}</p>
      <p><strong>Project Type:</strong> {project_type}</p>
      <p><strong>Property Type:</strong> {property_type}</p>
      <p><strong>Message:</strong><br>{message_content}</p>
    </body>
    </html>
    """

    # Send the email via SES
    try:
        response = ses_client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': [
                    RECIPIENT_EMAIL,
                ],
            },
            Message={
                'Subject': {
                    'Data': subject,
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Text': {
                        'Data': body_text,
                        'Charset': 'UTF-8'
                    },
                    'Html': {
                        'Data': body_html,
                        'Charset': 'UTF-8'
                    }
                }
            },
            ReplyToAddresses=[
                user_email,
            ]
        )
        logger.info(f"Email sent successfully. MessageId: {response['MessageId']}")
        # Prepare the response
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'  # Required for CORS support
            },
            'body': json.dumps({
                'message': f'Hello, {name}! Your form has been submitted successfully.'
            })
        }
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'message': 'An error occurred while processing your request.'
            })
        }

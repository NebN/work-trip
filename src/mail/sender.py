import sendgrid
import os
from src import log
from sendgrid.helpers.mail import *


_logger = log.get_logger(__name__)


def send_message(to_address, subj, message):
    sg = sendgrid.SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
    sender = Email(os.environ.get('SENDGRID_USERNAME'))
    m = Mail(from_email=sender, subject=subj, to_emails=To(to_address),
             plain_text_content=Content("text/plain", message))
    response = sg.client.mail.send.post(request_body=m.get())
    _logger.debug('send_message status code %s', response.status_code)


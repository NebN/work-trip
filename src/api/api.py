import os

from flask import Flask, request
from itsdangerous import URLSafeSerializer, BadSignature

from src.log import logging
from src.mail import sender
from src.model import Email
from src.persistence import Database
from src import parsing
from . import slack

api = Flask(__name__)
_logger = logging.get_logger(__name__)


@api.route('/', methods=['GET'])
def get():
    return 'you are not supposed to be here'


@api.route('/', methods=['POST'])
def post():
    return slack.respond(f'hello {request.values["user_name"]}')


'''
Register an email with the service.
This is used when receiving emails with attachments
to be able to know whom they are owned by.

Usage:
/register mail@email.com

Extra characters are allowed before or after the email.
'''
@api.route('/register', methods=['POST'])
def register():
    text = request.values['text']
    address = parsing.parse_email_address(text)
    _logger.debug(f'register {text}')
    if not address:
        return slack.respond(f'email not found in {text}')
    else:
        with Database() as db:
            existing_email = db.get_email(address)
            if existing_email:
                _logger.debug('email %s already exists %s verified status=%s', address, existing_email.verified)
                return slack.respond(f'{address} already registered, verified status={existing_email.verified}')
            user_id = request.values['user_id']
            db.add_employee_if_not_exists(user_id, request.values['user_name'])

            serializer = URLSafeSerializer(os.getenv('SECRET_KEY'))
            verification_token = serializer.dumps(address, salt=os.getenv('SALT'))
            base_domain = os.getenv('BASE_DOMAIN')
            verification_link = f'{base_domain}/confirm/{verification_token}'
            db.add_email(Email(address=address, employee_user_id=user_id))
            _logger.debug('verification link %s', verification_link)
            sender.send_message(to_address=address, subj='TrasfertaBot verification',
                                message=f'click the following link to verify your address\n{verification_link}')
            return slack.respond(f'email registered, please click the verification link sent to {address}')


'''
Confirm the email by clicking the registration token
received after having used the /receive command.
'''
@api.route('/confirm/<token>')
def confirm(token):
    serializer = URLSafeSerializer(os.getenv('SECRET_KEY'))
    try:
        address = serializer.loads(token, salt=os.getenv('SALT'))
    except BadSignature:
        return 'confirmation link is not valid'

    with Database() as db:
        current_email = db.get_email(address)
        if current_email.verified:
            return f'{address} already verified'
        else:
            db.verify_email(address)
            return f'{address} verified successfully'


'''
Adds an expense to a date if specified, today if not.
A description can also be added.

Usages:
/add 28.5           # adds an expense of €28.50 to today
/add 28.5 15        # adds an expense of €28.50 to the last 15th of the month
/add 28.5 15/11     # adds an expense of €28.50 to the last 15th of November
'''
@api.route('/add', methods=['POST'])
def add():
    text = request.values['text']
    expense = parsing.parse_expense(text)
    if expense:
        with Database() as db:
            user_id = request.values['user_id']
            db.add_employee_if_not_exists(user_id, request.values['user_name'])
            expense.employee_user_id = user_id
            expense_id = db.add_expense(expense)
        return slack.respond(f'Expense added. Amount={expense.amount}, date={expense.payed_on}'
                             f'{f", description={expense.description}" if expense.description else ""}. '
                             f'If you wish to delete the expense use /delete {expense_id}.')
    else:
        return slack.respond('Could not parse expense information from your message. '
                             'Valid formats include:\n'
                             '/add 28.5\n'
                             '/add 28.5 15\n'
                             '/add 28.5 15/11\n'
                             'You can always add a description at the end of the message.')


'''
Deletes an expense with given id.
'''
@api.route('/delete', methods=['POST'])
def delete():
    expense_id = request.values['text'].strip()
    with Database() as db:
        expense = db.get_expense(expense_id)
        if not expense:
            return slack.respond(f'No expense with id {expense_id} found.')
        if expense.employee_user_id != request.values['user_id']:
            return slack.respond(f'This expense does not belong to you ({request.values["user_name"]}).')
        if db.delete_expense(expense_id):
            return slack.respond(f'Expense [{expense.amount} {expense.payed_on} {expense.description}] '
                                 f'deleted successfully.')
        return slack.respond('Something went wrong while deleting the expense.')


'''
TODO
Sends a recap of the desired month if specified, of last month if not.

Usage:
/recap october  # sends the recap for October
/recap current  # sends the recap for the current month
/recap          # sends the recap for the previous month
'''
@api.route('/recap', methods=['POST'])
def recap():
    return 'sending recap for %s' % request.values['text']


'''
TODO ish
Handles chat events:
- Messages sent to the Bot: replies with the same message appending 'to you'
- Files shared with the Bot: tries to parse the date of the document, if successful uploads it to Dropbox
'''
@api.route('/event', methods=['POST'])
def event():
    # return challenge required for Slack Event API
    challenge = request.get_json().get('challenge')
    if challenge:
        return challenge

    event_json = request.get_json()['event']
    event_type = event_json['type']

    if event_type == 'file_shared':
        return _handle_file_shared(event_json)
    elif event_type == 'message':
        return _handle_message(event_json)

    return '???'


def _handle_file_shared(event_json):
    file_id = event_json['file_id']
    return f'{slack.download_file(file_id)} downloaded'


def _handle_message(event_json):
    if event_json.get('subtype') == 'bot_message':
        return 'bot_message: no_op'

    text = event_json.get('text')  # figure out what these ghost messages are
    user = event_json.get('user')  # this avoids infinite loops (hopefully)

    if not text or not user:
        _logger.debug('message event with no text or no user %s', event_json)
        return '???'

    if not text.startswith('/'):
        slack.send_message(event_json['channel'], f'{text} to you')
    return 'ok'

import os
import threading
import json
from datetime import date

from flask import Flask, request
from itsdangerous import URLSafeSerializer, BadSignature
from prettytable import PrettyTable

from src import parsing
from src.log import logging
from src.mail import sender
from src.model import Email
from src.persistence import Database
from src.persistence import documents
from src.util import dateutil
from .slack import slack

api = Flask(__name__)
_logger = logging.get_logger(__name__)


@api.route('/', methods=['GET'])
def get():
    return 'you are not supposed to be here'


@api.route('/', methods=['POST'])
def post():
    return slack.in_channel(f'hello {request.values["user_name"]}')


@api.route('/register', methods=['POST'])
def register():
    """
    Register an email with the service.
    This is used when receiving emails with attachments
    to be able to know whom they are owned by.

    Usage:
    /register mail@email.com

    Extra characters are allowed before or after the email.
    """
    text = request.values['text']
    address = parsing.parse_email_address(text)
    _logger.debug(f'register {text}')
    if not address:
        return slack.in_channel(f'email not found in {text}')
    else:
        with Database() as db:
            existing_email = db.get_email(address)
            if existing_email:
                _logger.debug('email %s already exists %s verified status=%s', address, existing_email.verified)
                return slack.in_channel(f'{address} already registered, verified status={existing_email.verified}')
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
            return slack.in_channel(f'email registered, please click the verification link sent to {address}')


@api.route('/confirm/<token>')
def confirm(token):
    """
    Confirm the email by clicking the registration token
    received after having used the /receive command.
    """
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
            expense.id = expense_id
            return slack.respond_expense_added(expense)
    else:
        return slack.in_channel('Could not parse expense information from your message. '
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
            return slack.in_channel(f'No expense with id {expense_id} found.')
        if expense.employee_user_id != request.values['user_id']:
            return slack.in_channel(f'This expense does not belong to you ({request.values["user_name"]}).')
        if db.delete_expense(expense):
            return slack.in_channel(f'Expense [{expense}] deleted successfully.')
        return slack.in_channel('Something went wrong while deleting the expense.')


'''
Sends a recap of the desired month if specified, of last month if not.

Usage:
/recap october  # sends the recap for October
/recap current  # sends the recap for the current month
/recap          # sends the recap for the previous month
'''


@api.route('/recap', methods=['POST'])
def recap():
    text = request.values['text'].strip()
    download_files = 'files' in text.lower()

    if len(text) == 0:
        month = dateutil.minus_months(date.today(), 1).month
    else:
        month = dateutil.month_from_string(text)
        if not month:
            return slack.in_channel(f'Sorry, could not understand month from {text}')

    with Database() as db:
        start = dateutil.last_date_of_day_month(1, month)
        end = start.replace(day=dateutil.max_day_of_month(start))
        user_id = request.values['user_id']
        expenses = db.get_expenses(user_id, start, end)

        if download_files:
            expenses_with_files = list(filter(lambda x: x.proof_url is not None, expenses))
            _logger.debug(f'expenses_with_files: {len(expenses_with_files)}')
            if len(expenses_with_files) == 0:
                return slack.ephemeral(f'No files to send for {start.strftime("%Y-%m")}.')

            channel_id = request.values['channel_id']

            def _download():
                for exp in expenses_with_files:
                    file_path = documents.download(exp.proof_url)
                    slack.upload_file(file_path, channel_id,
                                      description=f'id={exp.id} {exp.payed_on} {exp.amount} {exp.description}')

            t = threading.Thread(target=_download)
            t.start()

            return slack.ephemeral(f'Sending files for {start.strftime("%Y-%m")}...\n')

        else:
            table = PrettyTable()
            table.field_names = ['id', 'date', 'amount', 'description', 'has attachment']
            for e in expenses:
                table.add_row([e.id, e.payed_on.strftime('%d'), e.amount,
                               e.description if e.description else '', e.proof_url is not None])

        return slack.respond_recap(start.strftime("%Y-%m"), table)


@api.route('/info', methods=['POST'])
def info():
    message = 'Available commands:\n' \
              '>/register\n' \
              'Register an email with the service\n' \
              'This is used when receiving emails with attachments\n' \
              'to be able to know whom they are owned by\n' \
              'Usages:\n' \
              '`/register mail@email.com`\n' \
              '\n' \
              '>/add\n' \
              'Adds an expense to a date if specified, to today if not.\n' \
              'A description can also be added.\n' \
              'Usages:\n' \
              '`/add 28.5`           # adds an expense of €28.50 to today\n' \
              '`/add 28.5 15`        # adds an expense of €28.50 to the last 15th of the month\n' \
              '`/add 28.5 15/11`     # adds an expense of €28.50 to the last 15th of November\n' \
              '\n' \
              '>/delete\n' \
              'Deletes the expense with given id\n' \
              'Usages:\n' \
              '`/delete 42`\n' \
              '\n' \
              '>/recap\n' \
              'Sends a recap of the desired month if specified, of last month if not. ' \
              '(Month can be shortened to it\'s first 3 letters, e.g.: Oct)\n' \
              'Usages:\n' \
              '`/recap oct(ober)` # sends the recap for October\n' \
              '`/recap cur(rent)` # sends the recap for the current month\n' \
              '`/recap`           # sends the recap for the previous month\n' \
              '\n' \
              'In addition to these commands you can upload a file representing an expense, ' \
              'this will have the same effect as `/add` if the file is supported'

    return message


@api.route('/event', methods=['POST'])
def event():
    """
    Handles chat events:
    - Messages sent to the Bot: replies with the same message appending 'to you'
    - Files shared with the Bot: tries to parse the date of the document,
    if successful uploads it to DropBox and adds an entry to the Expense table
    """
    # return challenge required for Slack Event API
    challenge = request.get_json().get('challenge')
    if challenge:
        return challenge

    event_json = request.get_json()['event']
    event_type = event_json['type']

    if event_json.get('subtype') == 'bot_message':
        return 'bot_message: no_op'
    if event_json.get('user_id') == os.getenv('BOT_USER_ID') or event_json.get('user') == os.getenv('BOT_USER_ID'):
        return 'bot_message: no_op'

    _logger.debug('request json %s' % request.get_json())

    handler = _empty_handler

    if event_type == 'file_shared':
        handler = _handle_file_shared
    elif event_type == 'message':
        handler = _handle_message

    t = threading.Thread(target=handler, args=(event_json,))
    t.start()

    # we are required to respond immediately to /event requests
    # or slack will send another request
    return 'ok'


@api.route('/action', methods=['POST'])
def action():
    payload = json.loads(request.values['payload'])
    _logger.info(payload)

    user_id = payload['user']['id']
    channel_id = payload['channel']['id']
    response_url = payload['response_url']
    action_requests = payload['actions']

    actions = [parsing.parse_action(req['value']) for req in action_requests]
    threads = [threading.Thread(target=a.execute, args=(user_id, channel_id, response_url)) for a in actions]

    for t in threads:
        t.start()

    return 'ok'


def _handle_file_shared(event_json):
    slack.post_message(event_json['channel_id'], 'Processing file...')

    file_id = event_json['file_id']
    file_path = slack.download_file(file_id)
    expense = parsing.parse_expense_from_file(file_path)
    if not expense:
        return slack.post_message(event_json['channel_id'],
                                  'Sorry, this kind of file is not supported. '
                                  'Currently supported files are:\n'
                                  '- Trenitalia ticket\n'
                                  '- Trenord ticket\n')

    user_id = event_json['user_id']
    proof_url = documents.upload(file_path, f'{user_id}/{expense.payed_on}')

    if not proof_url:
        return slack.post_message(event_json['channel_id'],
                                  'Sorry, there was a problem uploading the file')

    expense.employee_user_id = user_id
    expense.proof_url = proof_url
    with Database() as db:
        db.add_employee_if_not_exists(user_id)
        db.add_expense(expense)

    slack.respond_expense_added(expense)


def _handle_message(event_json):
    text = event_json.get('text')  # figure out what these ghost messages are
    user = event_json.get('user')  # this avoids infinite loops (hopefully)

    if not user or not text:
        _logger.debug('message event with no text or no user %s', event_json)
        return

    if not text.startswith('/'):
        slack.post_message(event_json['channel'], f'Hi, I\'m TrasfertaBot. '
                                                  f'Type `/info` to get additional information.')


def _empty_handler(event_json):
    _logger.warn('empty handler called with %s', event_json)

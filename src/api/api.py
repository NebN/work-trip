import os
import threading
import json
import re
from datetime import date

from flask import Flask, request
from itsdangerous import URLSafeSerializer, BadSignature

from src import parsing
from src.log import logging
from src.persistence import Database
from src.persistence import documents
from src.mail import ReceivedMail, sender
from src.model import Email
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
        return slack.in_channel(f'email not recognized from: {text}')
    else:
        with Database() as db:
            existing_email = db.get_email(address)
            if existing_email:
                _logger.debug('email %s already exists %s verified status=%s', address, existing_email.verified)
                if existing_email.verified:
                    return slack.in_channel(f'{address} already registered and verified.')
                else:
                    _send_verification_link(address)
                    return slack.in_channel(f'{address} already registered but still not verified, '
                                            f'a new verification link has been sent.')
            user_id = request.values['user_id']
            db.add_employee_if_not_exists(user_id, request.values['user_name'])
            db.add_email(Email(address=address, employee_user_id=user_id))

            _send_verification_link(address)

            return slack.in_channel(f'Email registered, please click the verification link sent to {address}')


def _send_verification_link(address):
    serializer = URLSafeSerializer(os.getenv('SECRET_KEY'))
    verification_token = serializer.dumps(address, salt=os.getenv('SALT'))
    base_domain = os.getenv('BASE_DOMAIN')
    verification_link = f'{base_domain}/confirm/{verification_token}'
    _logger.debug('verification link %s', verification_link)
    sender.send_message(to_address=address, subj='TrasfertaBot verification',
                        message=f'click the following link to verify your address\n{verification_link}')


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


@api.route('/add', methods=['POST'])
def add():
    """
    Adds an expense to a date if specified, today if not.
    A description can also be added.

    Usages:
    /add 28.5           # adds an expense of €28.50 to today
    /add 28.5 15        # adds an expense of €28.50 to the last 15th of the month
    /add 28.5 15/11     # adds an expense of €28.50 to the last 15th of November
    """
    text = request.values['text']
    user_id = request.values['user_id']
    expense = parsing.parse_expense(text, user_id=user_id)
    if expense:
        with Database() as db:
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


@api.route('/del', methods=['POST'])
@api.route('/delete', methods=['POST'])
def delete():
    """
    Deletes an expense (or list of expenses) with given id.
    """
    expense_ids = [ex_id.strip() for ex_id in request.values['text'].strip().split(',')]
    with Database() as db:
        responses = []
        for expense_id in expense_ids:
            expense = db.get_expense(expense_id)
            if not expense:
                responses.append(f'No expense with id {expense_id} found.')
            elif expense.employee_user_id != request.values['user_id']:
                responses.append(f'The expense with id {expense_id} '
                                 f'does not belong to you ({request.values["user_name"]}).')
            elif db.delete_expense(expense):
                responses.append(f'{expense.mrkdown()} deleted successfully.')
            else:
                responses.append('Something went wrong while deleting the expense.')

        return "\n".join(responses)


@api.route('/recap', methods=['POST'])
def recap():
    """
    Sends a recap of the desired month if specified, of last month if not.

    Usage:
    /recap october  # sends the recap for October
    /recap current  # sends the recap for the current month
    /recap          # sends the recap for the previous month
    """
    text = request.values['text'].strip()

    if not text:
        month = date.today().month
    else:
        month = dateutil.month_from_string(text)
        if not month:
            return slack.in_channel(f'Sorry, could not understand month from {text}')

    with Database() as db:
        start = dateutil.last_date_of_day_month(1, month)
        end = start.replace(day=dateutil.max_day_of_month(start))
        user_id = request.values['user_id']
        expenses = db.get_expenses(user_id, start, end)
        return slack.respond_recap(expenses)


@api.route('/info', methods=['POST'])
def info():
    message = 'Available commands:\n' \
              '>/register\n' \
              'Register an email with the Bot\n' \
              'This is used when receiving emails with attachments\n' \
              'to be able to know whom they are owned by\n' \
              'emails should be sent to *trasfertabot@email2webhook.com*\n' \
              'Usages:\n' \
              '`/register mail@email.com`\n' \
              '\n' \
              '>*/add*\n' \
              'Adds an expense to a date if specified, to today if not.\n' \
              'A description can also be added.\n' \
              'Usages:\n' \
              '`/add 28.5 description (optional)` \nadds an expense of €28.50 to today with a description\n' \
              '`/add 28.5 15`\nadds an expense of €28.50 to the last 15th of the month\n' \
              '`/add 28.5 yes(terday)`\nadds an expense of €28.50 to yesterday, text inside parentheses is optional\n' \
              '`/add 28.5 ier(i)`\nadds an expense of €28.50 to yesterday, text inside parentheses is optional\n' \
              '`/add 28.5 15/11`\nadds an expense of €28.50 to the last 15th of November\n' \
              '\n\n' \
              '>*/del*\n' \
              'Deletes the expense with given id\n' \
              'Usages:\n' \
              '`/del 42`\n' \
              '`/del 42,43,44`\n' \
              '\n\n' \
              '>*/recap*\n' \
              'Sends a recap of the desired month if specified, of the current month if not. ' \
              '(Month can be shortened to it\'s first 3 letters, e.g.: oct or ott)\n' \
              'Usages:\n' \
              '`/recap oct`\nsends the recap for October\n' \
              '`/recap pre`\nsends the recap for the previous month\n' \
              '`/recap`\nsends the recap for the current month\n' \
              '\n' \
              '*In addition to these commands you can upload a file representing an expense*, ' \
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

    _logger.debug('request json %s' % request.get_json())

    event_json = request.get_json()['event']
    event_type = event_json['type']
    event_subtype = event_json.get('subtype')

    if event_subtype in ['bot_message', 'message_deleted']:
        return 'no_op'
    if event_json.get('user_id') == os.getenv('BOT_USER_ID') or event_json.get('user') == os.getenv('BOT_USER_ID'):
        return 'bot_message: no_op'

    handler = _empty_handler

    if event_type == 'file_shared':
        handler = _handle_file_shared
    elif event_type == 'message' and event_subtype not in ['message_changed', 'file_share']:
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


@api.route('/mail', methods=['POST'])
def inbox():
    sent_by = request.values['sender']
    # this is necessary to clean up addresses when receiving mail redirected from Gmail
    match = re.match(r'''(\w+)\+caf_=.+(@.+)''', sent_by)
    if match:
        sent_by = "".join(match.groups())

    _logger.info('got email from %s', sent_by)
    m = ReceivedMail(request.values['content'])

    if sent_by == 'forwarding-noreply@google.com':
        _handle_gmail(m)
    else:
        _handle_regular_mail(m, sent_by)

    return 'ok'


def _handle_gmail(mail):
    body = mail.body()
    address = re.search(r'''(.+@.+\..+)\s+has requested to automatically forward mail''', body).group(1)
    code = re.search(r'''Confirmation code:\s+(\w+)\s?''', body).group(1)
    with Database() as db:
        email_record = db.get_email(address)
        if email_record:
            user_id = email_record.employee_user_id
            channel_id = _user_channel_from_id(user_id)
            if email_record.verified:
                slack.post_message(channel_id, 'It seems like you are trying to redirect some email to me '
                                               'from a gmail account, '
                                               f'you are going to need this confirmation code: {code}')
            else:
                slack.post_message(channel_id, 'It seems like you are trying to redirect some email to me '
                                               'from a gmail account, '
                                               f'the email you are using is still not verified.\n'
                                               'To receive a new verification link '
                                               f'type `/register {email_record.address}`')


def _handle_regular_mail(mail, sent_by):
    with Database() as db:
        email_record = db.get_email(sent_by)
        if not email_record:
            _logger.warn('received email from unrecognized address %s', sent_by)
        else:
            address = email_record.address
            user_id = email_record.employee_user_id
            channel_id = _user_channel_from_id(user_id)

            if not channel_id:
                _logger.error('cannot proceed handling email, channel_id is required')
            elif not email_record.verified:
                _logger.warn('received email from unverified address %s', address)
                slack.post_message(channel_id, f'Email received on {mail.date()} from {address}, '
                                               f'subject: {mail.subject()}.\n'
                                               f'This email is still not verified, '
                                               f'please verify it before using it with the Bot.\n'
                                               f'To receive a new verification link '
                                               f'type `/register {email_record.address}`')
            else:
                expenses = []
                failed = []
                for f in mail.attachments():
                    expense = parsing.parse_expense_from_file(f)
                    if not expense:
                        failed.append(os.path.basename(f))
                    else:
                        proof_url = documents.upload(f, f'{user_id}/{expense.payed_on}')
                        expense.proof_url = proof_url
                        expense.employee_user_id = user_id
                        pending_id = db.add_expense_pending(expense)
                        expense.id = pending_id
                        expenses.append(expense)

                slack.post_email_expenses(channel_id, expenses, failed)


def _user_channel_from_id(user_id):
    with Database() as db:
        user_record = db.get_employee(user_id)
        channel_id = user_record.channel_id
        if not channel_id:
            user_channel = slack.im_channel_of_user(user_record.user_id)
            if user_channel:
                channel_id = user_channel['id']
                user_record.channel_id = channel_id
                db.update_employee(user_record)
        return channel_id


def _handle_file_shared(event_json):
    channel_id = event_json['channel_id']
    ts = slack.post_message(channel_id, 'Processing file...')

    file_id = event_json['file_id']
    file_path = slack.download_file(file_id)
    expense = parsing.parse_expense_from_file(file_path)
    if not expense:
        return slack.update(channel_id, ts,
                            'Sorry, this kind of file is not supported. '
                            'Currently supported files are:\n'
                            '- Trenitalia ticket\n'
                            '- Trenord ticket\n')

    user_id = event_json['user_id']
    proof_url = documents.upload(file_path, f'{user_id}/{expense.payed_on}')
    with open(file_path, 'rb') as f:
        external_id = slack.file_add(title=str(expense), file_id=file_id, file_bytes=f.read())

    if not proof_url or not external_id:
        return slack.update(channel_id, ts,
                            'Sorry, there was a problem uploading the file')

    expense.employee_user_id = user_id
    expense.proof_url = proof_url
    expense.external_id = external_id

    with Database() as db:
        db.add_employee_if_not_exists(user_id)
        expense_id = db.add_expense(expense)

    expense.id = expense_id
    slack.update(channel_id, ts, 'File processed successfully.')
    return slack.post_expense_added(channel_id, expense)


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

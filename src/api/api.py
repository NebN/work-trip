import os
import threading
import json
from datetime import date

from flask import Flask, request
from prettytable import PrettyTable

from src import parsing
from src.log import logging
from src.persistence import Database
from src.persistence import documents
from src.util import dateutil, collectionutil
from .slack import slack

api = Flask(__name__)
_logger = logging.get_logger(__name__)


@api.route('/', methods=['GET'])
def get():
    return 'you are not supposed to be here'


@api.route('/', methods=['POST'])
def post():
    return slack.in_channel(f'hello {request.values["user_name"]}')


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
            if expense.employee_user_id != request.values['user_id']:
                responses.append(f'The expense with id {expense_id} '
                                 f'does not belong to you ({request.values["user_name"]}).')
            if db.delete_expense(expense):
                responses.append(f'Expense {expense} deleted successfully.')
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

    if len(text) == 0:
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

        expenses_by_week = map(lambda exp: (exp.payed_on.strftime('%V'), exp), expenses)
        tables = []
        for week_expenses in collectionutil.groupbykey(expenses_by_week):
            table = PrettyTable()
            table.field_names = ['id', 'date', 'amount', 'description', 'has attachment']

            for e in week_expenses:
                table.add_row([e.id, e.payed_on.strftime('%d'), e.amount,
                               e.description if e.description else '', e.proof_url is not None])
            tables.append(table.get_string())

        # if we have at least one expense create the final row section with the totals
        if len(expenses) > 0:
            total_table = PrettyTable()
            total_table.field_names = ['from', 'to', 'expenses', 'total amount', 'attachments']
            dates = list(map(lambda x: x.payed_on, expenses))
            from_value = min(dates)
            to_value = max(dates)
            expenses_value = len(expenses)
            total_amount_value = sum(map(lambda x: x.amount, expenses))
            attachments_value = len([ex for ex in expenses if ex.proof_url is not None])
            total_table.add_row([from_value, to_value, expenses_value, total_amount_value, attachments_value])

            tables.append(total_table)

        return slack.respond_recap(start.strftime("%Y-%m"), tables)


@api.route('/info', methods=['POST'])
def info():
    message = 'Available commands:\n' \
              '\n' \
              '>*/add*\n' \
              'Adds an expense to a date if specified, to today if not.\n' \
              'A description can also be added.\n' \
              'Usages:\n' \
              '`/add 28.5 description (optional)` \nadds an expense of €28.50 to today with a description\n' \
              '`/add 28.5 15`\nadds an expense of €28.50 to the last 15th of the month\n' \
              '`/add 28.5 15/11`\nadds an expense of €28.50 to the last 15th of November\n' \
              '\n\n' \
              '>*/delete*\n' \
              'Deletes the expense with given id\n' \
              'Usages:\n' \
              '`/delete 42`\n' \
              '`/delete 42,43,44`\n' \
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
    _logger.info(request)
    try:
        _logger.info(request.get_json())
    except Exception:
        _logger.info('no json')

    try:
        _logger.info(request.values)
    except Exception:
        _logger.info('no values')

    return 'ok'


def _handle_file_shared(event_json):
    ts = slack.post_message(event_json['channel_id'], 'Processing file...')

    file_id = event_json['file_id']
    file_path = slack.download_file(file_id)
    expense = parsing.parse_expense_from_file(file_path)
    if not expense:
        return slack.update(event_json['channel_id'], ts,
                            'Sorry, this kind of file is not supported. '
                            'Currently supported files are:\n'
                            '- Trenitalia ticket\n'
                            '- Trenord ticket\n')

    user_id = event_json['user_id']
    proof_url = documents.upload(file_path, f'{user_id}/{expense.payed_on}')
    with open(file_path, 'rb') as f:
        external_id = slack.file_add(title=str(expense), file_id=file_id, file_bytes=f.read())

    if not proof_url or not external_id:
        return slack.update(event_json['channel_id'], ts,
                            'Sorry, there was a problem uploading the file')

    expense.employee_user_id = user_id
    expense.proof_url = proof_url
    expense.external_id = external_id

    with Database() as db:
        db.add_employee_if_not_exists(user_id)
        db.add_expense(expense)

    return slack.update(event_json['channel_id'], ts,
                        f'Expense added {expense}')


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

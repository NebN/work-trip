import os
import json
import hashlib

import requests
from flask import jsonify
from prettytable import PrettyTable

from src.log import logging
from src.util import collectionutil
from .Button import Button

_logger = logging.get_logger(__name__)


def in_channel(text):
    return jsonify(
        response_type='in_channel',
        text=text
    )


def ephemeral(text):
    return jsonify(
        response_type='ephemeral',
        text=text
    )


def update(channel_id, ts, text):
    req_url = 'https://slack.com/api/chat.update'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'channel': channel_id,
        'text': text,
        'ts': ts
    }
    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok or not resp_json['ok']:
        _logger.error(f'could not update message %s %s with %s, response=%s', channel_id, ts, text, resp_json)
    else:
        _logger.error(f'updated message %s %s with %s', channel_id, ts, text)


def replace_original(text, url):
    payload = {
        'replace_original': 'true',
        'text': text
    }
    resp = requests.post(url, json=payload)
    resp_json = resp.json()
    if not resp.ok:
        _logger.error(f'could not replace original message with %s to %s, response=%s', text, url, resp_json)
    else:
        _logger.debug('replaced message with %s to %s', text, url)


def respond_expense_added(expense):
    return jsonify(
        response_type='in_channel',
        blocks=_build_expense_added_blocks(expense)
    )


def post_expense_added(channel_id, expense):
    post_message(channel_id, blocks=json.dumps(_build_expense_added_blocks(expense)))


def respond_recap(expenses):
    return jsonify(
        response_type='in_channel',
        blocks=_build_recap_blocks(expenses)
    )


def post_recap(channel_id, expenses):
    post_message(channel_id, blocks=json.dumps(_build_recap_blocks(expenses)))


def ask_download(channel_id, year_month):
    blocks = [
        _buttons(
            Button(text='Download multiple files', value=f'download {year_month}', style='primary'),
            Button(text='Download as single file', value=f'download -m {year_month}', style='primary')
        )
    ]
    post_message(channel_id=channel_id, blocks=json.dumps(blocks))


def post_ephemeral(channel_id, user_id, text):
    req_url = 'https://slack.com/api/chat.postEphemeral'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'channel': channel_id,
        'user': user_id,
        'text': text,
    }
    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok or not resp_json['ok']:
        _logger.error(f'could not post ephemeral %s to %s for user %s, response=%s',
                      text, channel_id, user_id, resp_json)
    else:
        _logger.debug('posted ephemeral %s to %s for %s', text, channel_id, user_id)


def post_message(channel_id, text=None, blocks=None):
    req_url = 'https://slack.com/api/chat.postMessage'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'channel': channel_id,
    }

    if text:
        params['text'] = text

    if blocks:
        params['blocks'] = blocks
        _logger.debug('blocks %s', blocks)

    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok or not resp_json['ok']:
        _logger.error(f'could not post message %s to %s, response=%s', text, channel_id, resp_json)
    else:
        _logger.debug('posted message %s to %s', text, channel_id)
        return resp_json['message']['ts']


def file_info(file_id):
    req_url = f'https://slack.com/api/files.info'
    token = os.environ['BOT_USER_OAUTH_TOKEN']
    params = {
        'token': token,
        'file': file_id
    }

    _logger.debug('requesting file %s', file_id)

    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok:
        _logger.warn('cannot request file link, response=%s', resp)
        return None
    else:
        return resp_json['file']


def download_file(file_id):
    info = file_info(file_id)
    download_url = info['url_private_download']
    filename = info['name']

    _logger.debug('downloading file %s from %s', filename, download_url)

    token = os.environ['BOT_USER_OAUTH_TOKEN']
    resp = requests.get(download_url, headers={'Authorization': 'Bearer ' + token})
    if not resp.ok:
        _logger.warn('cannot download file, response=%s', resp)
        return None
    else:
        with open(filename, 'wb') as file:
            file.write(resp.content)

    return filename


def file_upload(file_path, channel_id, description, unfurl=None):
    req_url = f'https://slack.com/api/files.upload'
    with open(file_path, 'rb') as f:
        file = {
            'file': (file_path, f)
        }

        params = {
            'token': os.environ['BOT_USER_OAUTH_TOKEN'],
            'initial_comment': description,
            'channels': [channel_id],
        }

        if unfurl is not None:
            params['unfurl_links'] = unfurl
            params['unfurl_media'] = unfurl

        _logger.debug('uploading file %s', file_path)

        resp = requests.post(req_url, params=params, files=file)
        resp_json = resp.json()
        if not resp.ok or not resp_json['ok']:
            _logger.warn('cannot upload file, response=%s', resp_json)
            return None
        else:
            return resp_json['file']['id']


def file_add(title, file_id, file_bytes=None):
    token = os.environ['BOT_USER_OAUTH_TOKEN']
    info = file_info(file_id)

    if file_bytes is None:
        download_url = info['url_private_download']
        file_resp = requests.get(download_url, headers={'Authorization': 'Bearer ' + token})
        file_bytes = file_resp.content

    url = info['url_private']
    external_id = hashlib.md5(file_bytes).hexdigest()

    req_url = 'https://slack.com/api/files.remote.add'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'external_url': url,
        'external_id': external_id,
        'title': title
    }

    resp = requests.get(req_url, params=params)
    resp_json = resp.json()

    if not resp.ok or not resp_json['ok']:
        _logger.warn('cannot add file, response=%s', resp_json)
        return None
    else:
        return external_id


def file_share(channel_id, external_id):
    req_url = 'https://slack.com/api/files.remote.share'

    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'channels': channel_id,
        'external_id': external_id
    }

    _logger.debug('sharing file %s to %s', external_id, channel_id)

    resp = requests.get(req_url, params=params)
    resp_json = resp.json()

    if not resp.ok or not resp_json['ok']:
        _logger.warn('cannot share file, response=%s', resp_json)
        return False
    else:
        return True


def post_email_expenses(user_channel, expenses, failed):
    if not [e for e in expenses if e]:
        post_message(user_channel, 'An email was received from an address registered by you, '
                                   'but no expenses were able to be parsed.\n'
                                   'Currently supported files are:\n'
                                   '- Trenitalia ticket\n'
                                   '- Trenord ticket\n')
    else:
        blocks = [[
            _text_section(f'{expense.no_id()} received via email, do you wish to add it?'),
            _buttons(
                Button(text='Confirm', value=f'expense c {expense.id}', style='primary'),
                Button(text='Discard', value=f'expense d {expense.id}', style='danger')
            )
        ] for expense in expenses]

        post_message(user_channel, blocks=json.dumps(*blocks))


def user_info(user_id):
    req_url = f'https://slack.com/api/users.info'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'user': user_id,
    }

    _logger.debug('requesting info on %s', user_id)

    resp = requests.post(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok:
        _logger.warn('cannot get info on user, response=%s', resp_json)
        return None
    else:
        return resp_json['user']


def im_channel_of_user(user_id):
    req_url = f'https://slack.com/api/users.conversations'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'user': user_id,
        'types': 'im'
    }

    _logger.debug('requesting channel info for user %s', user_id)

    resp = requests.post(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok:
        _logger.warn('cannot get channel info for user %s, response=%s', user_id, resp_json)
        return None
    else:
        channels = resp_json['channels']
        if not channels:
            _logger.warn('no im channels for found for user %s, response=%s', user_id, resp_json)
            return None
        else:
            return channels[0]


def _text_section(text):
    return {
        'type': 'section',
        'text': {
            'text': text,
            'type': 'mrkdwn'
        }
    }


def _buttons(*bs):
    return {
        'type': 'actions',
        'elements': [_button(b) for b in bs]
    }


def _button(b):
    button_dict = {
        'type': 'button',
        'value': b.value,
        'text': {
            'type': 'plain_text',
            'emoji': True,
            'text': b.text
        }
    }

    if b.style:
        button_dict['style'] = b.style

    return button_dict


def _build_expense_added_blocks(expense):
    return [
        _text_section(f'Added {expense.mrkdown()}'),
        _buttons(
            Button(text='Delete', value=f'delete {expense.id}', style='danger'),
            Button(text='Recap', value=f'recap {expense.payed_on.strftime("%Y-%m")}', style='primary')
        )
    ]


def _build_recap_blocks(expenses):
    if not expenses:
        return [
            _text_section('No expenses found.')
        ]
    else:
        expense_tables = _expense_tables_from_expenses(expenses)
        year_month = expenses[0].payed_on.strftime('%Y-%m')
        return [
            _text_section(f'*Recap for {year_month}*'),
            *[_text_section(f'```{e}```') for e in expense_tables],
            _buttons(
                Button(text='Download Attachments', value=f'ask -download {year_month}'),
                Button(text='Download as Html', value=f'html {year_month}', style='primary'),
                Button(text='Destroy the Planet', value='destroy', style='danger')
            )
        ]


def _expense_tables_from_expenses(expenses):
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
    if expenses:
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
        return tables

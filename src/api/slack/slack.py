import os

import requests
from flask import jsonify

from src.log import logging
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


def respond_expense_added(expense):
    expense_string = f'*Amount:* {expense.amount}\n' \
                     f'*Date:* {expense.payed_on}\n'

    if expense.description:
        expense_string = expense_string + f'*Description*: {expense.description}'

    return jsonify(
        response_type='in_channel',
        blocks=[
            _text_section('*Expense added.*'),
            _text_section(expense_string),
            _buttons(
                Button(text='Delete', value=f'delete {expense.id}', style='danger')
            )
        ]
    )


def respond_recap(year_month, expenses_table):
    return jsonify(
        response_type='in_channel',
        blocks=[
            _text_section(f'*Recap for {year_month}*'),
            _text_section(f'```{expenses_table}```'),
            _buttons(
                Button(text='Download Attachments', value=f'download {year_month}', style='primary'),
                Button(text='Destroy the Planet', value='destroy', style='danger')
            )
        ]
    )


def send_message(target, text):
    req_url = 'https://slack.com/api/chat.postMessage'
    params = {
        'token': os.environ['BOT_USER_OAUTH_TOKEN'],
        'channel': target,
        'text': text,
    }
    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok or not resp_json['ok']:
        _logger.error(f'could not send message %s to %s, response=%s', text, target, resp_json)
    else:
        _logger.debug('sent message %s to %s, ephemeral=%s', text, target, 'False')


def download_file(file_id):
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
        download_url = resp_json['file']['url_private_download']
        filename = resp_json['file']['name']

        _logger.debug('downloading file %s from %s', filename, download_url)

        file_resp = requests.get(download_url, headers={'Authorization': 'Bearer ' + token})
        if not resp.ok:
            _logger.warn('cannot download file, response=%s', resp_json)
            return None
        else:
            with open(filename, 'wb') as file:
                file.write(file_resp.content)

        return filename


def upload_file(file_path, channel_id, description):
    req_url = f'https://slack.com/api/files.upload'
    with open(file_path, 'rb') as f:
        file = {
            'file': (file_path, open(file_path, 'rb'))
        }

        params = {
            'token': os.environ['BOT_USER_OAUTH_TOKEN'],
            'initial_comment': description,
            'channels': [channel_id],
        }

        _logger.debug('uploading file %s', file_path)

        resp = requests.post(req_url, params=params, files=file)
        resp_json = resp.json()
        if not resp.ok:
            _logger.warn('cannot upload file, response=%s', resp_json)
            return None
        else:
            return resp_json['file']['url_private']


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
        'style': b.style,
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

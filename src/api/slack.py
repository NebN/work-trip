import os

import requests
from flask import jsonify

from src.log import logging

_logger = logging.get_logger(__name__)


def respond(text):
    return jsonify(
        response_type='in_channel',
        text=text
    )


def ephemeral(text):
    return jsonify(
        response_type='ephemeral',
        text=text
    )


def monospaced(text, title=None):
    t = f'{title}\n' if title else ''
    return jsonify(
        response_type='in_channel',
        blocks=[{
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': f'{t}```{text}```'
            }
        }]
    )


def send_message(target, text):
    req_url = 'https://slack.com/api/chat.postMessage'
    params = {
        "token": os.environ['BOT_USER_OAUTH_TOKEN'],
        "channel": target,
        "text": text,
    }
    resp = requests.get(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok or not resp_json['ok']:
        _logger.error(f'could not send message %s to %s, response=%s', text, target, resp_json)
    else:
        _logger.debug('sent message %s to %s, ephemeral=%s', text, target, ephemeral)


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
            "token": os.environ['BOT_USER_OAUTH_TOKEN'],
            "initial_comment": description,
            "channels": [channel_id],
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
        "token": os.environ['BOT_USER_OAUTH_TOKEN'],
        "user": user_id,
    }

    _logger.debug('requesting info on %s', user_id)

    resp = requests.post(req_url, params=params)
    resp_json = resp.json()
    if not resp.ok:
        _logger.warn('cannot get info on user, response=%s', resp_json)
        return None
    else:
        return resp_json['user']

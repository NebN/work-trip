import requests
import os
from flask import jsonify
from src.log import logging

_logger = logging.get_logger(__name__)


def respond(text):
    return jsonify(
        response_type='in_channel',
        text=text
    )


def send_message(channel, text):
    token = os.environ['BOT_USER_OAUTH_TOKEN']
    req_url = f'https://slack.com/api/chat.postMessage?token={token}&channel={channel}&text={text}'
    resp = requests.get(req_url)
    if not resp.ok or not resp.json()['ok']:
        _logger.error(f'could not send message %s to %s, response=%s', text, channel, resp)
    else:
        _logger.debug('sending message %s to %s', text, channel)


def download_file(file_id):
    token = os.environ['BOT_USER_OAUTH_TOKEN']
    req_url = f'https://slack.com/api/files.info?token={token}&file={file_id}'
    resp = requests.get(req_url)
    resp_json = resp.json()
    if not resp.ok:
        _logger.warn('cannot request file link, response=%s', resp)
        return 'something went wrong'
    else:
        download_url = resp_json['file']['url_private_download']
        filename = resp_json['file']['name']
        _logger.info('downloading file %s from %s', filename, download_url)
        file_resp = requests.get(download_url, headers={'Authorization': 'Bearer ' + token})
        if not resp.ok:
            _logger.warn('cannot download file, response=%s', resp)
            return 'something went wrong'
        else:
            with open(filename, 'wb') as file:
                file.write(file_resp.content)

        return filename

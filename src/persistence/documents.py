import os
import dropbox
from dropbox.exceptions import ApiError
from src.log import logging

_logger = logging.get_logger(__name__)
_dbox = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))


def upload(filename, save_path):
    with open(filename, 'rb') as f:
        try:
            res = _dbox.files_upload(f.read(), f'/{save_path}/{filename}')
            return res.path_display
        except ApiError as e:
            _logger.error(f'could not upload file %s', e)


def download(path):
    metadata, res = _dbox.files_download(path)
    download_path = f'{metadata.id.replace(":", "")}_{metadata.name}'
    with open(download_path, 'wb') as file:
        file.write(res.content)
    return download_path


def delete(path):
    try:
        metadata = _dbox.files_delete_v2(path)
        return f'Successfully deleted file {metadata.metadata.name}'
    except ApiError:
        return f'Error while deleting {path}'


def temp_download_link(path):
    try:
        resp = _dbox.files_get_temporary_link(path)
        return resp.link
    except ApiError as e:
        _logger.error('could not get temporary download link for %s, cause: %s', path, e)

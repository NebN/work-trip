import os
import dropbox
from src.log import logging

_logger = logging.get_logger(__name__)

dbox = dropbox.Dropbox(os.getenv('DROPBOX_ACCESS_TOKEN'))

_logger.info(dbox.users_get_current_account())

for entry in dbox.files_list_folder('/2019-12-11/').entries:
    _logger.info(entry.name)

# with open('ticket.pdf') as file:
#   dbox.files_upload(file, '/2019-12-12/ticket.pdf')

with open('downloaded_ticket.pdf', 'wb') as file:
    metadata, res = dbox.files_download('/2019-12-10/ticket.pdf')
    _logger.info(metadata)
    file.write(res.content)





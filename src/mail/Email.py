import datetime
import email
import os

from src import log
from src import parsing


class Email:

    def __init__(self, email_bytes):
        self.logger = log.get_logger(__name__)
        self._email = email.message_from_bytes(email_bytes)
        self.subject = self._email['Subject']
        date_tuple = email.utils.parsedate_tz(self._email['Date'])
        self.date = datetime.datetime.fromtimestamp(email.utils.mktime_tz(date_tuple))
        self.sender, self.sender_email = email.utils.parseaddr(self._email['From'])
        year, month, day = self.date.strftime('%Y,%m,%d').split(',')
        self.download_path = os.path.join('downloads', year, month, day)

    def get_first_text_block(self):
        maintype = self._email.get_content_maintype()
        if maintype == 'multipart':
            for part in self._email.get_payload():
                if part.get_content_maintype() == 'text':
                    return part.get_payload()
        elif maintype == 'text':
            return self._email.get_payload()

    def download_attachments(self, allowed_files=None):
        def ok_to_download(filename):
            if allowed_files is None:
                return True
            else:
                return filename.split('.')[-1] in allowed_files

        attachments = [p for p in self._email.walk() if p.get_content_type() == 'application/octet-stream']
        for attachment in attachments:
            filename = attachment.get_filename()
            if ok_to_download(filename):
                self.logger.info('downloading attachment %s from mail %s', filename, self.subject)
                os.makedirs(self.download_path, exist_ok=True)
                file_path = os.path.join(self.download_path, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'wb') as path:
                        path.write(attachment.get_payload(decode=True))
                else:
                    self.logger.warn('attachment already downloaded to %s', file_path)

                print(parsing.parse_expense_from_file(file_path))
            else:
                self.logger.info('not downloading file because not allowed: %s, allowed extensions: %s',
                                 filename, allowed_files)

    def print_summary(self):
        print('date %s' % str(self.date))
        print('subj %s' % self.subject)
        print('from %s (%s)' % (self.sender, self.sender_email))

    def print(self):
        print('date %s' % str(self.date))
        print('subj %s' % self.subject)
        print('from %s (%s)' % (self.sender, self.sender_email))
        print(self.get_first_text_block())

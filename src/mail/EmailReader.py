import imaplib
import datetime
from src import log
from .Email import Email


class EmailReader:

    def __init__(self, domain, address, password):
        self.logger = log.get_logger(__name__)
        self._domain = 'imap.%s' % domain
        self._address = address
        self._password = password

    def __enter__(self):
        self.logger.info('connecting to %s as %s', self._domain, self._address)
        self._conn = imaplib.IMAP4_SSL(self._domain)
        self._conn.login(self._address, self._password)
        self.logger.info('connected')
        self._conn.select('inbox')
        return self

    def __exit__(self, *args):
        self.logger.info('disconnecting from %s %s ...', self._domain, self._address)
        self._conn.close()
        self._conn.logout()

    def search_ids(self, query):
        self.logger.info('searching for mail %s', query)
        _, data = self._conn.uid('search', None, query)
        return data[0].split()

    def emails_from_ids(self, ids):
        emails = []

        for id in ids:
            self.logger.info('downloading email with UID %s', id)
            response, data = self._conn.uid('fetch', id, '(RFC822)')
            if response == 'OK':
                email = Email(data[0][1])
                emails.append(email)
            else:
                self.logger.warn('response was NOT OK: %s', response)

        return emails

    def ids_of_mail_from_date(self, date):
        date = date.strftime('%d-%b-%Y')
        return self.search_ids('(ON %s)' % date)

    def ids_of_mail_from_today(self):
        return self.ids_of_mail_from_date(datetime.date.today())

    def read(self):
        date = (datetime.date.today() - datetime.timedelta(5)).strftime('%d-%b-%Y')
        # ids = self.ids_of_mail_from_date(datetime.date.fromisoformat('2019-12-02'))
        ids = self.ids_of_mail_from_date(datetime.date.fromisoformat('2019-12-06'))
        # ids = self.ids_of_mail_from_today()
        # ids = self.search_ids('(SENTSINCE %s)' % date)
        emails = self.emails_from_ids(ids)
        for email in emails:
            email.print_summary()
            email.download_attachments(allowed_files=['pdf'])


'''
ids = data[0]  # data is a list.
id_list = ids.split()  # ids is a space separated string
latest_email_id = id_list[-1]  # get the latest

result, data = self.conn.fetch(latest_email_id, "(RFC822)")  # fetch the email body (RFC822) for the given ID
email = Email(data[0][1])
'''

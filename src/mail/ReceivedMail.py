import os
import re
import email


class ReceivedMail:
    def __init__(self, raw):
        self._msg = email.message_from_string(raw)

    def subject(self):
        return self._msg['subject']

    def sent_from(self):
        return email.utils.parseaddr(self._msg['from'])[-1]

    def sent_to(self):
        return self._msg['to']

    def date(self):
        return self._msg['date']

    @classmethod
    def _attachments_dir(cls):
        if 'attachments' not in os.listdir('.'):
            os.mkdir('attachments')
        return os.path.join('.', 'attachments')

    def attachments(self):
        downloaded_attachments = []
        for part in self._msg.walk():
            if part.get_content_maintype() not in ['multipart', 'text']:
                filename = part.get_filename()

                if filename:
                    path = os.path.join(ReceivedMail._attachments_dir(), filename)
                    with open(path, 'wb') as fp:
                        fp.write(part.get_payload(decode=True))
                        downloaded_attachments.append(path)

        return downloaded_attachments

    def body(self):
        if not self._msg.is_multipart():
            return self._msg.get_payload()
        else:
            maintype = self._msg.get_content_maintype()
            if maintype == 'multipart':
                for part in self._msg.get_payload():
                    if part.get_content_maintype() == 'text':
                        return part.get_payload()
                return ""
            elif maintype == 'text':
                return self._msg.get_payload()

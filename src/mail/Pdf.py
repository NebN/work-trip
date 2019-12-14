import io
import re
import datetime
import locale
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage


class Pdf:

    TRENORD_PATTERN='''(\d{2}\s\w{3}\s\d{4})'''
    TRENITALIA_PATTERN='''Ore \d{2}:\d{2}\s-\s(\d{2}/\d{2}/\d{4})'''

    # Trenord
    # 10 dic 2019
    # (\d{2}\s\w{3}\s\d{4})

    # Trenitalia
    # Ore 19:37 - 13/12/2019
    # Ore \d{2}:\d{2}\s-\s(\d{2}/\d{2}/\d{4})

    def __init__(self, path):
        resource_manager = PDFResourceManager()
        out = io.StringIO()
        device = TextConverter(resource_manager, outfp=out, laparams=LAParams())
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(resource_manager, device)

        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)

        self._text = out.getvalue()

        fp.close()
        device.close()
        out.close()

    def find(self):
        found_trenitalia = re.findall(Pdf.TRENITALIA_PATTERN, self._text)
        found_trenord = re.findall(Pdf.TRENORD_PATTERN, self._text)

        print('found_trenitalia %s' % found_trenitalia)
        print('found_trenord %s' % found_trenord)

        locale.setlocale(locale.LC_ALL, 'it_IT.utf8')

        for italia in found_trenitalia:
            date_time_obj = datetime.datetime.strptime(italia, '%d/%m/%Y')
            print(date_time_obj)

        for nord in found_trenord:
            date_time_obj = datetime.datetime.strptime(nord, '%d %b %Y')
            print(date_time_obj)

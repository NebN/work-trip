import io

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage


def file_to_text(path=None, file=None):
    extension = path.split('.')[-1]
    if extension == 'pdf':
        return _pdf_to_text(path, file)


def _pdf_to_text(path=None, file=None):
    fp = file if file else open(path, 'rb')

    resource_manager = PDFResourceManager()
    out = io.StringIO()
    device = TextConverter(resource_manager, outfp=out, laparams=LAParams())
    interpreter = PDFPageInterpreter(resource_manager, device)

    for page in PDFPage.get_pages(fp):
        interpreter.process_page(page)

    text = out.getvalue()

    fp.close()
    device.close()
    out.close()

    return text

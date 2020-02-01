import os
from PyPDF2 import PdfFileMerger
from PyPDF2 import PdfFileReader
from PIL import Image


def extension(path):
    return os.path.splitext(path)[1]


def merge_to_pdf(paths, name=None):
    filename = name if name else 'merged.pdf'

    pdfs = [p for p in paths if extension(p) == '.pdf']
    not_pdfs = [p for p in paths if extension(p) != '.pdf']

    if len(not_pdfs) > 0:
        img = Image.open(not_pdfs[0])
        other_images = [Image.open(p) for p in not_pdfs[1:]]
        img.save(filename, 'PDF', save_all=True, append_images=other_images)
        pdfs.append(filename)

    merger = PdfFileMerger()
    for path in pdfs:
        with open(path, 'rb') as f:
            merger.append(PdfFileReader(f))

    merger.write(filename)

    return os.path.join(os.getcwd(), filename)

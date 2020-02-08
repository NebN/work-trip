import os
from mako.template import Template
from src import PRJ_ROOT


def render(date_start, date_end, expenses):
    with open(os.path.join(PRJ_ROOT, *['res', 'html', 'mako_recap.html'])) as template:
        return Template(template.read()).render(date_start=date_start, date_end=date_end, expenses=expenses)

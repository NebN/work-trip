import locale
import re
from datetime import date, datetime

from src.model import Expense
from src.util import dateutil
from src.api.slack import DownloadAttachments, DeleteExpense, Ask, HtmlRecap, DestroyPlanet, slack
from src.log import logging
from .IncrementalParser import IncrementalParser
from .file_to_text import file_to_text


_logger = logging.get_logger(__name__)


def parse_expense(text, user_id=None):
    """
    /add 28.5           # adds an expense of €28.50 to today
    /add 28.5 15        # adds an expense of €28.50 to the last 15th of the month
    /add 28.5 15/11     # adds an expense of €28.50 to the last 15th of November
    """
    ip = IncrementalParser(text)
    # amount
    amount_search = ip.extract('''(\d+(?:[\.,]\d+)?)''')
    if amount_search:
        amount = amount_search[0]

        # payed_on
        if ip.text().lower().startswith('yes') or ip.text().lower().startswith('ier'):
            timezone_offset = slack.user_info(user_id)['tz_offset']
            user_date = dateutil.plus_seconds(datetime.utcnow().date(), timezone_offset)
            payed_on = dateutil.plus_days(user_date, -1)
            ip.extract('''(\w+)''')
        else:
            date_search = ip.extract('''(\d{1,2}(?:[/-]\d{1,2})?)''')
            try:
                payed_on = _interpret_day(date_search[0]) if date_search else date.today()
            except ValueError:
                return None

        # description
        description_search = ip.extract('''(.+)''')
        description = description_search[0] if description_search else None
        return Expense(payed_on=payed_on, amount=amount, description=description)


def parse_expense_from_file(path):
    text = file_to_text(path)

    # Trenord
    # 10 dic 2019

    # Trenitalia
    # Ore 19:37 - 13/12/2019

    if text:
        found_trenitalia = re.search('''Ore \d{2}:\d{2}\s-\s(\d{2}/\d{2}/\d{4})''', text)
        if found_trenitalia:
            date_time = datetime.strptime(found_trenitalia.group(1), '%d/%m/%Y')
            amount = re.search(''': (\d{1,2}\.\d{2}) €''', text).group(1)
            description = 'Trenitalia ticket'
            return Expense(payed_on=date_time.date(), amount=amount, description=description)

        found_trenord = re.search('''(\d{2}\s\w{3}\s\d{4})''', text)
        if found_trenord:
            locale.setlocale(locale.LC_ALL, 'it_IT.utf8')
            date_time = datetime.strptime(found_trenord.group(1), '%d %b %Y')
            amount = re.search('''(\d{1,2},\d{2}) €''', text).group(1).replace(',', '.')
            description = 'Trenord ticket'
            return Expense(payed_on=date_time.date(), amount=amount, description=description)


def parse_action(text):
    _logger.info('parsing action from %s', text)

    ip = IncrementalParser(text)
    action_name = ip.extract('''(\w+)''')[0]

    if action_name == 'ask':
        question = ip.extract('''(-)(\w+)''')[1]
        return Ask(question=question, request_text=ip.text())

    elif action_name == 'download':
        merge = ip.extract('''(-m)''') is not None
        year, month = ip.extract('''(\d{4})-(\d{2})''')
        date_start = date(int(year), int(month), 1)
        date_end = date_start.replace(day=dateutil.max_day_of_month(date_start))
        return DownloadAttachments(date_start=date_start, date_end=date_end, merge=merge)

    elif action_name == 'delete':
        expense_id = ip.extract('''(\d+)''')[0]
        return DeleteExpense(expense_id=expense_id)

    elif action_name == 'html':
        year, month = ip.extract('''(\d{4})-(\d{2})''')
        date_start = date(int(year), int(month), 1)
        date_end = date_start.replace(day=dateutil.max_day_of_month(date_start))
        return HtmlRecap(date_start=date_start, date_end=date_end)

    elif action_name == 'destroy':
        return DestroyPlanet()


def _interpret_day(text):
    day_pattern = '''\s*(\d{1,2})[/-]?(\d{1,2})?\s*'''
    ip = IncrementalParser(text)
    day_search = ip.extract(day_pattern)
    if day_search:
        day = int(day_search[0])
        month = int(day_search[1]) if day_search[1] else None
        if month:
            return dateutil.last_date_of_day_month(day, month)
        else:
            return dateutil.last_date_of_day(day)

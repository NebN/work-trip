import re
from datetime import date
from src.model import Expense
from src.util import dateutil
from .IncrementalParser import IncrementalParser


def parse_email_address(text):
    pattern = '''.*?(\S+@\S+\.\S+).*'''
    search = re.search(pattern, text)
    if search:
        return search.group(1)


'''
/add 28.5           # adds an expense of €28.50 to today
/add 28.5 15        # adds an expense of €28.50 to the last 15th of the month
/add 28.5 15/11     # adds an expense of €28.50 to the last 15th of November
'''
def parse_expense(text):
    ip = IncrementalParser(text)
    amount_search = ip.extract('''(\d+(?:[\.,]\d+)?)''')
    date_search = ip.extract('''(\d{1,2}(?:[/-]\d{1,2})?)''')
    description_search = ip.extract('''(.+)''')

    if amount_search:
        amount = amount_search[0]
        try:
            payed_on = interpret_day(date_search[0]) if date_search else date.today()
        except ValueError:
            return None
        description = description_search[0] if description_search else None
        return Expense(employee_user_id=None, payed_on=payed_on, amount=amount, description=description)


def interpret_day(text):
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



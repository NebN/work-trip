import re
from datetime import date
from src.model import Expense
from src.util import dateutil


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
    expense_pattern = '''\s*(\d+(?:[\.\,]?\d+))\s*(\S+)?'''
    expense_search = re.search(expense_pattern, text)

    if expense_search:
        amount = expense_search.group(1)
        payed_on = interpret_day(expense_search.group(2)) if expense_search.group(2) else date.today()
        return Expense(employee_user_id=None, payed_on=payed_on, amount=amount)


def interpret_day(text):
    day_pattern = '''\s*(\d{1,2})[/-]?(\d{1,2})?\s*'''
    day_search = re.search(day_pattern, text)
    if day_search:
        day = int(day_search.group(1))
        if len(day_search.groups()) == 2:
            month = int(day_search.group(2))
            return dateutil.last_date_of_day_month(day, month)
        else:
            return dateutil.last_date_of_day(day)



from datetime import datetime, date, timedelta


def last_date_of_day(day_number):
    today = date.today()
    if today.day >= day_number:
        return today.replace(day=day_number)
    else:
        return (today.replace(day=1) - timedelta(days=1)).replace(day=day_number)


def last_date_of_day_month(day_number, month_number):
    computed_date = date.today().replace(month=month_number, day=day_number)

    if computed_date > date.today():
        computed_date = computed_date.replace(year=computed_date.year - 1)

    return computed_date

def plus_seconds(d, seconds):
    return d + timedelta(seconds=seconds)

def plus_days(d, days):
    return d + timedelta(days=days)

def minus_months(d, months):
    computed_date = d
    for n in range(0, months):
        computed_date = (computed_date.replace(day=1) - timedelta(days=1))

    max_day = max_day_of_month(computed_date)
    return computed_date.replace(day=min(max_day, d.day))


def max_day_of_month(d):
    # example:
    # date = 2019/02/15
    # following_month = 2019/02/1 + 31 days = 2019/03/04
    # returned = (2019/03/04 - 4).day = (2019/02/28).day = 28
    following_month_date = d.replace(day=1) + timedelta(days=31)
    return (following_month_date - timedelta(following_month_date.day)).day


def dates_in_year_month(year, month):
    return [date(year, month, n) for n in range(1, max_day_of_month(date(year, month, 1)) + 1)]


def dates_in_previous_year_month():
    today = date.today()
    last_month_today = minus_months(today, 1)
    return dates_in_year_month(last_month_today.year, last_month_today.month)


def dates_in_current_year_month():
    today = date.today()
    year = today.year
    month = today.month
    max_day = today.day
    return [date(year, month, n) for n in range(1, max_day + 1)]


def start_and_end_date_from_year_month_string(ymstring):
    d = datetime.strptime(ymstring, '%Y-%m').date()
    return d, d.replace(day=max_day_of_month(d))


def month_from_string(text):
    if len(text) < 3:
        return None
    s = text[0:3].lower()
    if s == 'cur' or s == 'att':
        return date.today().month
    if s == 'pre':
        return minus_months(date.today(), 1).month
    if s == 'jan' or s == 'gen':
        return 1
    if s == 'feb':
        return 2
    if s == 'mar':
        return 3
    if s == 'apr':
        return 4
    if s == 'may' or s == 'mag':
        return 5
    if s == 'jun' or s == 'giu':
        return 6
    if s == 'jul' or s == 'lug':
        return 7
    if s == 'aug' or s == 'ago':
        return 8
    if s == 'sep' or s == 'set':
        return 9
    if s == 'oct' or s == 'ott':
        return 10
    if s == 'nov':
        return 11
    if s == 'dec' or s == 'dic':
        return 12



from datetime import timedelta
from datetime import date


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


def minus_months(date, months):
    computed_date = date
    for n in range(0, months):
        computed_date = (computed_date.replace(day=1) - timedelta(days=1))

    max_day = max_day_of_month(computed_date)
    return computed_date.replace(day=min(max_day, date.day))


def max_day_of_month(date):
    # example:
    # date = 2019/02/15
    # following_month = 2019/02/1 + 31 days = 2019/03/04
    # returned = (2019/03/04 - 4).day = (2019/02/28).day = 28
    following_month_date = date.replace(day=1) + timedelta(days=31)
    return (following_month_date - timedelta(following_month_date.day)).day
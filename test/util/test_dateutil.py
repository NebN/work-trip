import unittest
from datetime import date, timedelta
from src.util import dateutil


class DateUtilTests(unittest.TestCase):

    def test_minus_months(self):
        self.assertEqual(date(2019, 2, 28),
                         dateutil.minus_months(date(2019, 10, 31), 8))

        self.assertEqual(date(2018, 11, 15),
                         dateutil.minus_months(date(2019, 2, 15), 3))

    def test_last_date_of_day(self):
        today = date.today()
        self.assertEqual(today,
                         dateutil.last_date_of_day(today.day))

        tomorrow = (today + timedelta(days=1))
        self.assertEqual(dateutil.minus_months(tomorrow, 1),
                         dateutil.last_date_of_day(tomorrow.day))

    def test_last_date_of_day_month(self):
        today = date.today()
        self.assertEqual(today,
                         dateutil.last_date_of_day_month(today.day, today.month))

        tomorrow = (today + timedelta(days=1))
        self.assertEqual(dateutil.minus_months(tomorrow, 12),
                         dateutil.last_date_of_day_month(tomorrow.day, tomorrow.month))

    def test_max_day_of_month(self):
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 1, 1)))
        self.assertEqual(28, dateutil.max_day_of_month(date(2019, 2, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 3, 1)))
        self.assertEqual(30, dateutil.max_day_of_month(date(2019, 4, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 5, 1)))
        self.assertEqual(30, dateutil.max_day_of_month(date(2019, 6, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 7, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 8, 1)))
        self.assertEqual(30, dateutil.max_day_of_month(date(2019, 9, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 10, 1)))
        self.assertEqual(30, dateutil.max_day_of_month(date(2019, 11, 1)))
        self.assertEqual(31, dateutil.max_day_of_month(date(2019, 12, 1)))
        self.assertEqual(29, dateutil.max_day_of_month(date(2020, 2, 1)))

    def test_month_from_string(self):
        self.assertIsNone(dateutil.month_from_string('a'))
        self.assertEqual(date.today().month, dateutil.month_from_string('cur'))
        self.assertEqual(1, dateutil.month_from_string('january'))
        self.assertEqual(1, dateutil.month_from_string('Gen'))
        self.assertEqual(2, dateutil.month_from_string('feb'))
        self.assertEqual(2, dateutil.month_from_string('Febbraio'))
        self.assertEqual(8, dateutil.month_from_string('Aug'))
        self.assertEqual(9, dateutil.month_from_string('set'))

    def test_dates_in_year_month(self):
        dates_in_september = [date(2019, 9, n) for n in range(1, 30 + 1)]
        self.assertEqual(dates_in_september, dateutil.dates_in_year_month(2019, 9))

        dates_in_october = [date(2019, 10, n) for n in range(1, 31 + 1)]
        self.assertEqual(dates_in_october, dateutil.dates_in_year_month(2019, 10))

        dates_in_feb_2019 = [date(2019, 2, n) for n in range(1, 28 + 1)]
        self.assertEqual(dates_in_feb_2019, dateutil.dates_in_year_month(2019, 2))

        dates_in_feb_2020 = [date(2020, 2, n) for n in range(1, 29 + 1)]
        self.assertEqual(dates_in_feb_2020, dateutil.dates_in_year_month(2020, 2))
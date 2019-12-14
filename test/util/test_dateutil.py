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
        self.assertEqual(dateutil.max_day_of_month(date(2019, 1, 1)),   31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 2, 1)),   28)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 3, 1)),   31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 4, 1)),   30)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 5, 1)),   31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 6, 1)),   30)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 7, 1)),   31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 8, 1)),   31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 9, 1)),   30)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 10, 1)),  31)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 11, 1)),  30)
        self.assertEqual(dateutil.max_day_of_month(date(2019, 12, 1)),  31)
        self.assertEqual(dateutil.max_day_of_month(date(2020, 2, 1)),   29)

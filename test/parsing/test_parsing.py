import unittest
from datetime import date

from src.parsing import *


class ParsingTests(unittest.TestCase):
    def test_parse_email_address(self):
        expected_address = 'first.last@email.com'
        self.assertEqual(parse_email_address('first.last@email.com'), expected_address)
        self.assertEqual(parse_email_address('asd first.last@email.com'), expected_address)
        self.assertEqual(parse_email_address('first.last@email.com asd'), expected_address)
        self.assertEqual(parse_email_address(' first.last@email.com'), expected_address)
        self.assertEqual(parse_email_address('first.last@email.com '), expected_address)
        self.assertEqual(parse_email_address(' first.last@email.com '), expected_address)
        self.assertEqual(parse_email_address('first.last@email.com abc def'), expected_address)
        self.assertEqual(parse_email_address('abc def first.last@email.com'), expected_address)
        self.assertEqual(parse_email_address('abc def first.last@email.com abc def'), expected_address)

    def test_parse_email_address_malformed(self):
        self.assertIsNone(parse_email_address('first.lastemail.com'))
        self.assertIsNone(parse_email_address('first.last@emailcom'))
        self.assertIsNone(parse_email_address('first.lastemailcom'))
        self.assertIsNone(parse_email_address('@email.com'))

    def test_parse_expense_only_amount(self):
        expense = parse_expense(' 29.95')
        self.assertEqual(expense.amount, '29.95')
        self.assertEqual(expense.payed_on, date.today())

    def test_parse_expense_day_month(self):
        expense = parse_expense(' 29.95 24/1 some description')
        self.assertEqual(expense.amount, '29.95')
        self.assertEqual(expense.payed_on, date(2019, 1, 24))
        self.assertEqual(expense.description, 'some description')

    def test_parse_expense_day(self):
        today = date.today()
        last_date_with_day_24 = today.replace(day=24) if today.day >= 24 else today.replace(day=24, month=today.month-1)
        expense = parse_expense(' 29.95 24 some description')
        self.assertEqual(expense.amount, '29.95')
        self.assertEqual(expense.payed_on, last_date_with_day_24)
        self.assertEqual(expense.description, 'some description')

    def test_parse_expense_amount_same_as_day(self):
        today = date.today()
        last_date_with_day_24 = today.replace(day=24) if today.day >= 24 else today.replace(day=24, month=today.month-1)
        expense = parse_expense(' 24 24 some description')
        self.assertEqual(expense.amount, '24')
        self.assertEqual(expense.payed_on, last_date_with_day_24)
        self.assertEqual(expense.description, 'some description')

    def test_parse_expense_weird_cases(self):
        expense1 = parse_expense('24/12 some description')
        self.assertEqual('/12 some description', expense1.description)

        expense2 = parse_expense('24 some description')
        self.assertEqual(date.today(), expense2.payed_on)
        self.assertEqual('some description', expense2.description)

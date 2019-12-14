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

    def test_parse_expense(self):
        expense = parse_expense(' 29.95 24/1 asd')
        self.assertEqual(expense.amount, '29.95')
        self.assertEqual(expense.payed_on, date(2019, 1, 24))


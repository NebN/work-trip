import os
import psycopg2
from src import log
from src.model import *
from src.api import slack
from . import documents


class Database:

    def __init__(self):
        self.logger = log.get_logger(__name__)
        self._conn_url = os.environ.get('DATABASE_URL')
        self._sslmode = os.environ.get('SSLMODE', default='require')

    def __enter__(self):
        self.logger.info('connecting to database... sslmode %s', self._sslmode)
        self._conn = psycopg2.connect(self._conn_url, sslmode=self._sslmode)
        self.logger.info('connected')
        return self

    def __exit__(self, *args):
        self.logger.info('disconnecting from database...')
        self._conn.commit()
        self._conn.close()

    def get_employee(self, user_id):
        cur = self._conn.cursor()
        cur.execute('SELECT user_id, user_name, channel_id '
                    'FROM employee '
                    'WHERE user_id = %s', (user_id,))
        res = cur.fetchone()
        if res:
            return Employee(user_id=res[0], user_name=res[1], channel_id=res[2])
        self.logger.warn('Employee not found with user_id %s', user_id)
        return None

    def get_expense(self, expense_id):
        cur = self._conn.cursor()
        cur.execute('SELECT id, employee_user_id, payed_on, amount, description, proof_url '
                    'FROM expense '
                    'WHERE id = %s', (expense_id, ))
        res = cur.fetchone()
        if res:
            self.logger.debug('Expense found %s', res)
            return Expense(id=res[0], employee_user_id=res[1], payed_on=res[2],
                           amount=res[3], description=res[4], proof_url=res[5])
        self.logger.warn('Expense not found with id %s', expense_id)
        return None

    def get_expenses(self, user_id, date_from, date_to=None):
        to = date_to if date_to else date_from
        cur = self._conn.cursor()
        cur.execute('SELECT id, employee_user_id, payed_on, amount, description, proof_url, external_id '
                    'FROM expense '
                    'WHERE employee_user_id = %s AND payed_on BETWEEN %s AND %s '
                    'ORDER BY payed_on, id',
                    (user_id, date_from, to))
        res = cur.fetchall()
        self.logger.debug('Expenses found %s', res)
        return [Expense(id=r[0], employee_user_id=r[1], payed_on=r[2], amount=r[3],
                        description=r[4], proof_url=r[5], external_id=r[6]) for r in res]

    def update_expense(self, expense):
        self.logger.debug('updating expense %s', expense)
        cur = self._conn.cursor()
        cur.execute('UPDATE expense '
                    'SET employee_user_id=%s, payed_on=%s, amount=%s, description=%s, proof_url=%s, external_id=%s '
                    'WHERE id=%s', (expense.employee_user_id, expense.payed_on, expense.amount, expense.description,
                                    expense.proof_url, expense.external_id, expense.id))
        return cur.statusmessage.endswith('1')

    def add_employee_if_not_exists(self, user_id, user_name=None):
        if not self.get_employee(user_id):
            name = user_name if user_name else slack.user_info(user_id)['name']
            employee = Employee(user_id, name)
            self.logger.debug('adding new Employee following request: %s', employee)
            self.add_employee(employee)

    def add_employee(self, employee):
        cur = self._conn.cursor()
        self.logger.info('adding %s', employee)
        cur.execute('INSERT INTO employee (user_id, user_name, channel_id) VALUES (%s, %s, %s)',
                    (employee.user_id, employee.user_name, employee.channel_id))

    def add_expense(self, expense):
        cur = self._conn.cursor()
        self.logger.info('adding %s', expense)
        cur.execute('INSERT INTO expense (employee_user_id, payed_on, amount, description, proof_url, external_id) '
                    'VALUES (%s, %s, %s, %s, %s, %s) '
                    'RETURNING id',
                    (expense.employee_user_id, expense.payed_on, expense.amount,
                     expense.description, expense.proof_url, expense.external_id))
        return cur.fetchone()[0]

    def delete_expense_with_id(self, expense_id):
        expense = self.get_expense(expense_id)
        return self.delete_expense(expense)

    def delete_expense(self, expense):
        cur = self._conn.cursor()
        self.logger.info('deleting expense with id %s', expense.id)
        cur.execute('DELETE FROM expense WHERE id = %s', (expense.id,))

        if expense.proof_url and not self.proof_url_is_still_needed(expense.proof_url):
            documents.delete(expense.proof_url)

        return cur.statusmessage.endswith('1')

    def proof_url_is_still_needed(self, proof_url):
        cur = self._conn.cursor()
        self.logger.info('looking for proof_url to see if it\'s still needed %s', proof_url)
        cur.execute('SELECT COUNT(1) '
                    'FROM expense '
                    'WHERE proof_url = %s '
                    'LIMIT 1', (proof_url,))
        return cur.fetchone()[0] == 1

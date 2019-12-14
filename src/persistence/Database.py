import psycopg2
import os
from src import log
from src.model import *


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
        cur.execute('SELECT * FROM employee WHERE user_id = %s', (user_id,))
        res = cur.fetchone()
        if res:
            return Employee(user_id=res[0], user_name=res[1], channel_id=res[2])
        self.logger.warn('Employee not found with user_id %s', user_id)
        return None

    def get_email(self, address):
        cur = self._conn.cursor()
        cur.execute('SELECT * FROM email WHERE address = %s', (address,))
        res = cur.fetchone()
        if res:
            self.logger.debug('Email found %s', res)
            return Email(address=res[0], employee_user_id=res[1], verified=res[2])
        self.logger.warn('Email not found with address %s', address)
        return None

    def get_expenses(self, user_id, datefrom, dateto=None):
        to = dateto if dateto else datefrom
        cur = self._conn.cursor()
        cur.execute('SELECT * FROM expense WHERE employee_user_id = %s AND payed_on BETWEEN %s AND %s',
                    (user_id, datefrom, to))
        res = cur.fetchall()
        self.logger.debug('Expenses found %s', res)
        return [Expense(id=r[0], employee_user_id=r[1], payed_on=r[2], amount=r[3], description=r[4], proof_url=r[5])
                for r in res]

    def add_employee(self, employee):
        cur = self._conn.cursor()
        self.logger.info('adding %s', employee)
        cur.execute('INSERT INTO employee (user_id, user_name, channel_id) VALUES (%s, %s, %s)',
                    (employee.user_id, employee.user_name, employee.channel_id))

    def add_email(self, email):
        cur = self._conn.cursor()
        self.logger.info('adding %s', email)
        cur.execute('INSERT INTO email (address, employee_user_id, verified) VALUES (%s, %s, %s)',
                    (email.address, email.employee_user_id, email.verified))

    def verify_email(self, address):
        cur = self._conn.cursor()
        self.logger.info('verifying Email %s', address)
        cur.execute('UPDATE email SET verified = true WHERE address = %s', (address,))

    def add_expense(self, expense):
        cur = self._conn.cursor()
        self.logger.info('adding %s', expense)
        cur.execute('INSERT INTO expense (employee_user_id, payed_on, amount, description, proof_url) '
                    'VALUES (%s, %s, %s, %s, %s)',
                    (expense.employee_user_id, expense.payed_on, expense.amount,
                     expense.description, expense.proof_url))

    def delete_expense(self, id):
        cur = self._conn.cursor()
        self.logger.info('deleting expense with id %s', id)
        cur.execute('DELETE FROM expense WHERE id = %s', (id,))

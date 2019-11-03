import psycopg2
from src import log


class Database:

    def __init__(self, conn_url, sslmode):
        self.logger = log.get_logger(__name__)
        self.logger.info('connecting to database...')
        self._conn = psycopg2.connect(conn_url, sslmode=sslmode)

    def test(self):
        cur = self._conn.cursor()
        cur.execute('SELECT 1')
        print(cur.fetchone())
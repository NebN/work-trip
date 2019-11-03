from src import log
import os
from dotenv import load_dotenv
from src.persistence import Database

load_dotenv()
email = os.getenv('EMAIL')
email_password = os.getenv('EMAIL_PASSWORD')
domain = os.getenv('EMAIL_DOMAIN')

logger = log.get_logger(__name__)

database_url = os.getenv('DATABASE_URL')
sslmode = os.getenv('SSLMODE', default='required')

db = Database(database_url, sslmode)
db.test()

# with EmailReader(domain, email, email_password) as reader:
#     reader.read()

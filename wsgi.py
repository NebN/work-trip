import os
from datetime import timedelta
import dotenv
from src.api import api
from src.log import logging
from src.util.ScheduledTask import ScheduledTask
import requests

_logger = logging.get_logger(__name__)

dotenv.load_dotenv()
api = api

if os.environ.get('STAY_AWAKE', default='true') == 'true':
    # Heroku's free tier machines shut down after 30 minutes of inactivity,
    # this should prevent that from happening
    def stay_awake():
        resp = requests.get('https://work-trip-bot.herokuapp.com/')
        _logger.debug('stay_awake status code %s', resp.status_code)


    scheduled = ScheduledTask(task=stay_awake, timedelta=timedelta(minutes=28))

    try:
        scheduled.start(delay_in_seconds=10)
    except KeyboardInterrupt:
        scheduled.stop()

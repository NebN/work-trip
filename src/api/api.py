from flask import Flask, request
from src import log

logger = log.get_logger(__name__)
logger.info('starting Flask app...')
app = Flask(__name__)

@app.route('/', methods=['POST'])
def test():
    args = str(request.args)
    logger.info('args received %s' % args)
    return f'response to post request'



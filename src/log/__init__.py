import yaml
from logging import config
from .logging import get_logger

yaml_cfg = yaml.safe_load(open('../logging.yaml'))
logging_cfg = yaml_cfg['logging']
config.dictConfig(logging_cfg)


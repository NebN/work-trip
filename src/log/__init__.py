import yaml
import sys
from logging import config
from .logging import get_logger

try:
    yaml_cfg = yaml.safe_load(open('logging.yaml'))
    logging_cfg = yaml_cfg['logging']
    config.dictConfig(logging_cfg)
except FileNotFoundError:
    sys.stderr.write('[WARNING] could not load yaml logging configuration\n')

__all__ = ['logging']

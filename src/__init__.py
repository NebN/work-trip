import os

__all__ = ['api', 'PRJ_ROOT']

SRC_ROOT = os.path.dirname(os.path.abspath(__file__))
PRJ_ROOT = os.path.normpath(SRC_ROOT + os.sep + os.pardir)

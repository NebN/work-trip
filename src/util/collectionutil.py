import itertools
import operator


def groupbykey(collection):
    # sort for faster operations on big collections
    seq = list(collection)
    seq.sort(key=operator.itemgetter(0))
    grouped = itertools.groupby(seq, operator.itemgetter(0))
    return [([v[1] for v in vs]) for (k, vs) in grouped]

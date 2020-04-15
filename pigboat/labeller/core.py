# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02_labeller.core.ipynb (unless otherwise specified).

__all__ = ['UniqueList', 'Labeller', 'tasks_labels']

# Cell
from fastai2.basics import *
from ..basics import *
from functools import wraps

# Cell
class UniqueList(L):
    def append(self, o):
        if o not in self.items: super().append(o)

# Cell
class Labeller:
    def __init__(self, abstain='abstain'):
        self.func_order,self.abstain = UniqueList(),abstain
        self.subs = L()

    def __call__(self, tfm):
        def _inner(f):
            self.func_order.clear()
            sub = subscribe(tfm, self.func_order)
            self.subs.append(sub)
            return sub(self._add_label(f))
        return _inner

    def listen(self, v):
        for sub in self.subs: sub.listen = v

    def _add_label(self, f):
        @wraps(f)
        def _inner(x):
            label = ifnone(f(x), self.abstain)
            x = add_attr(x, 'labels', [])
            x.labels.append(label)
            return x
        return _inner

# Cell
def tasks_labels(tls, vocab, splits=None, lazy=False):
    tasks = TfmdLists(tls, [AttrGetter('labels'), MultiCategorize(vocab)], splits=splits)
    if not lazy: tasks.cache()
    return tasks
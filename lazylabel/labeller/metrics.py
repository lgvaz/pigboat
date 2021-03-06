# AUTOGENERATED! DO NOT EDIT! File to edit: nbs/02a_labeller.metrics.ipynb (unless otherwise specified).

__all__ = ['LabelMetric', 'ValidLabelMetric', 'Coverage', 'Polarity', 'CountCorrect', 'CountIncorrect', 'LabelAccuracy']

# Cell
from fastai2.basics import *
from ..basics import *
from .core import Labeller

# Cell
class LabelMetric:
    def reset(self): raise NotImplementedError
    def accumulate(self, xb): raise NotImplementedError
    @property
    def value(self): raise not ImplementedError
    @property
    def name(self): return self.__class__.__name__

# Cell
class ValidLabelMetric(LabelMetric):
    def accumulate(self, xb, yb): raise NotImplementedError

# Cell
class Coverage(LabelMetric):
    def reset(self): self.total,self.count = 0,0
    def accumulate(self, xb):
        #TODO: Hardcoded 0 for abstain, can be wrong
        self.total += find_bs(xb)
        bcount = (xb!=0).sum(axis=0)
        self.count += bcount
    @property
    def value(self):
        pcts = (100*self.count.float()/self.total).tolist()
        return [f'{pct:.2f}% ({v})' for pct,v in zip(pcts,self.count)]

# Cell
class Polarity(LabelMetric):
    def reset(self): self._unique = None
    def accumulate(self, xb):
        bpol = L(set(t.unique().tolist()) for t in xb.unbind(dim=1))
        if self._unique is None: self._unique = bpol
        else:
            for i in range_of(bpol): self._unique[i].update(bpol[i])
    @property
    def value(self): return self.unique.map(len)

    @property
    def unique(self):
        unique = self._unique.copy()
        unique.map(self._discard_abstain)
        return unique
    def _discard_abstain(self, o): return o.discard(0) #TODO: abstain

# Cell
class CountCorrect(ValidLabelMetric):
    def reset(self): self.count = 0
    def accumulate(self, xb, yb): self.count += (xb==yb).sum(dim=0) # TODO: abstain
    @property
    def value(self): return self.count.tolist()
    @property
    def name(self): return 'Correct'

# Cell
class CountIncorrect(CountCorrect):
    def accumulate(self, xb, yb):
        self.count += ((xb!=0)&(xb!=yb)).sum(dim=0) # TODO: abstain
    @property
    def name(self): return 'Incorrect'

# Cell
class LabelAccuracy(ValidLabelMetric):
    def reset(self): self.count,self.total = 0,0
    def accumulate(self, xb, yb):
        self.total += (xb!=0).sum(dim=0) # TODO: abstain
        self.count += (xb==yb).sum(dim=0)
    @property
    def value(self): return (self.count.float()/self.total).tolist()
    @property
    def name(self): return 'Accuracy'

# Cell
defaults.labeller_metrics = [Coverage, Polarity, LabelAccuracy, CountCorrect, CountIncorrect]

# Cell
_old_labeller_init = Labeller.__init__
@patch
def __init__(self:Labeller, metrics=None):
    _old_labeller_init(self)
    self.metrics = L(instantiate(o) for o in L(metrics)+L(defaults.labeller_metrics))

# Cell
@patch
def summary(self:Labeller, dl):
    metrics = self.metrics
    for metric in metrics: metric.reset()
    for b in dl:
        xb,yb = split_batch(dl, b)
        for metric in metrics:
            if not isinstance(metric, ValidLabelMetric): metric.accumulate(xb); continue
            if yb is not None:                   metric.accumulate(xb,yb.view(-1,1)) # Safe to add dim in yb?
    if yb is None: metrics = metrics.filter(lambda o: not isinstance(o, ValidLabelMetric))
    data = dict(metrics.map(lambda o: (o.name, o.value)))
    return pd.DataFrame(data, index=self.lfs_order)
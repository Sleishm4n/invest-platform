"""
Generates the external, human-legible identifier for a model_runs row.

Format: {model_version}_{train_end:%Y%m%d}_{8-char random suffix}
e.g. "logreg_v1_20260706_7b9b8cfe"

The date component makes it legible in logs/filenames (at a glance: which
model, trained through which date). The random suffix exists purely so that
retraining the same model_version on the same train_end date doesn't collide
with model_runs.run_id's unique constraint -- without it, two runs on the
same day would be indistinguishable and the second insert would fail.
"""

import datetime as dt
import uuid


def generate_run_id(model_version: str, train_end: dt.date) -> str:
    suffix = uuid.uuid4().hex[:8]
    return f"{model_version}_{train_end:%Y%m%d}_{suffix}"
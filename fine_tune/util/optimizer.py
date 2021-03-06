r"""Helper functions for loading optimizer.

Usage:
    import fine_tune

    optimizer = fine_tune.util.load_optimizer(...)
    optimizer = fine_tune.util.load_optimizer_by_config(...)
"""

# built-in modules

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from typing import Tuple

# 3rd party modules

import torch
import torch.optim

# my own modules

import fine_tune.config
import fine_tune.model


def load_optimizer(
        betas: Tuple[float, float],
        eps: float,
        lr: float,
        model: fine_tune.model.Model,
        weight_decay: float
) -> torch.optim.AdamW:
    r"""Load `torch.optim.AdamW` optimizer.

    Args:
        betas:
            Optimizer `torch.optim.AdamW`'s beta coefficients.
        eps:
            Optimizer `torch.optim.AdamW`'s epsilon.
        lr:
            Optimizer `torch.optim.AdamW`'s learning rate.
        model:
            Model name of the current experiment.
        weight_decay:
            Optimizer `torch.optim.AdamW` weight decay regularization.

    Returns:
        AdamW optimizer.
    """
    # Remove weight decay on bias and layer-norm.
    no_decay = ['bias', 'LayerNorm.weight']
    optimizer_grouped_parameters = [
        {
            'params': [
                param for name, param in model.named_parameters()
                if not any(nd in name for nd in no_decay)
            ],
            'weight_decay': weight_decay,
        },
        {
            'params': [
                param for name, param in model.named_parameters()
                if any(nd in name for nd in no_decay)
            ],
            'weight_decay': 0.0,
        },
    ]

    return torch.optim.AdamW(
        optimizer_grouped_parameters,
        lr=lr,
        betas=betas,
        eps=eps
    )


def load_optimizer_by_config(
        config: fine_tune.config.BaseConfig,
        model: fine_tune.model.Model
) -> torch.optim.AdamW:
    r"""Load AdamW optimizer.

    Args:
        config:
            Configuration object which contains attributes
            `lr`, `betas`, `eps` and `weight_decay`.
        model:
            Source parameters to be optimized.

    Returns:
        Same as `fine_tune.util.load_optimizer`.
    """

    return load_optimizer(
        betas=config.betas,
        eps=config.eps,
        lr=config.lr,
        model=model,
        weight_decay=config.weight_decay
    )

r"""Helper function for training model.

Usage:
    fine_tune.util.train(...)
"""

# built-in modules

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from typing import Union

# 3rd party modules

import torch
import torch.nn as nn
import torch.utils
import torch.utils.data
import torch.utils.tensorboard
import transformers

from tqdm import tqdm

# my own modules

import fine_tune.config
import fine_tune.task
import fine_tune.model
import fine_tune.path


def train(
        config: Union[
            fine_tune.config.StudentConfig,
            fine_tune.config.TeacherConfig,
        ],
        dataset: Union[
            fine_tune.task.MNLI,
        ],
        is_distill: bool,
        model: Union[
            fine_tune.model.TeacherAlbert,
            fine_tune.model.TeacherBert,
        ],
        optimizer: torch.optim.AdamW,
        scheduler: torch.optim.lr_scheduler.LambdaLR,
        tokenizer: Union[
            transformers.AlbertTokenizer,
            transformers.BertTokenizer,
        ]
):
    r"""Fine-tune or distill model on task specific dataset.

    Args:
        config:
            `fine_tune.config.TeacherConfig` which attributes are used
            for experiment setup.
        dataset:
            Task specific dataset.
        is_distill:
            Whether to perform distillation.
        model:
            Model which will be fine-tuned on `dataset`.
        optimizer:
            AdamW optimizer.
        schduler:
            Linear warmup scheduler.
        tokenizer:
            Tokenizer paired with `model`.
    """

    # Training mode.
    model.train()

    # Clean all gradient.
    optimizer.zero_grad()

    # Get experiment name and path.
    if is_distill:
        experiment_name = fine_tune.config.StudentConfig.format_experiment_name(
            experiment=config.experiment,
            student=config.student,
            task=config.task
        )
    else:
        experiment_name = fine_tune.config.TeacherConfig.format_experiment_name(
            experiment=config.experiment,
            task=config.task,
            teacher=config.teacher
        )
    experiment_path = '{}/{}'.format(
        fine_tune.path.FINE_TUNE_EXPERIMENT,
        experiment_name
    )

    # Create dataloader.
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size=config.batch_size // config.accumulation_step,
        collate_fn=dataset.create_collate_fn(
            max_seq_len=config.max_seq_len,
            tokenizer=tokenizer
        ),
        shuffle=True
    )

    # Create tensorboard's `SummaryWriter`.
    writer = torch.utils.tensorboard.SummaryWriter(
        '{}/{}'.format(
            fine_tune.path.LOG,
            experiment_name
        )
    )

    if is_distill:
        # Use both hard-target and soft-target as objective.
        objective = fine_tune.objective.distill
    else:
        # Use Cross-Entropy as objective.
        objective = nn.CrossEntropyLoss()

    # Accumulation step counter.
    # Only useful when `config.accumulate_step > 1`.
    accumulate_step_counter = 0

    # Enumerate `config.epoch` times.
    for epoch in range(config.epoch):
        # Calculate accumulation loss.
        # Only update when accumulate to `config.batch_size`.
        accumulation_loss = 0

        # Enumerate `math.ceil(len(dataset) / config.batch_size)` times.
        # Use `torch.utils.data.DataLoader` to sample dataset.
        mini_batch_iterator = tqdm(
            dataloader,
            f'epoch: {epoch}, loss: {0:.6f}'
        )
        for (
                input_ids,
                attention_mask,
                token_type_ids,
                label,
                soft_target
        ) in mini_batch_iterator:

            if is_distill:
                # Mini-batch hard-target + soft-target loss.
                # Use `model(...)` to do forward pass.
                loss = objective(
                    pred=model(
                        input_ids=input_ids.to(config.device),
                        token_type_ids=token_type_ids.to(config.device),
                        attention_mask=attention_mask.to(config.device)
                    ),
                    hard_target=label.to(config.device),
                    soft_target=soft_target.to(config.device)
                )
            else:
                # Mini-batch Cross-Entropy loss.
                # Use `model(...)` to do forward pass.
                loss = objective(
                    model(
                        input_ids=input_ids.to(config.device),
                        token_type_ids=token_type_ids.to(config.device),
                        attention_mask=attention_mask.to(config.device)
                    ),
                    label.to(config.device)
                )

            # Loss must be divided by `config.accumulation_step`
            # to achieve actual mini-batch size.
            accumulation_loss += loss / config.accumulation_step

            # Increment accumulation step
            accumulate_step_counter += 1

            # Perform gradient descend when achieve actual mini-batch size
            # or current mini-batch is the last mini-batch in the epoch.
            if accumulate_step_counter % config.accumulation_step == 0 \
                    or input_ids.size(0) < config.batch_size:
                # Backward pass.
                accumulation_loss.backward()

                # Gradient clipping.
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    config.max_norm
                )

                # Gradient descend.
                optimizer.step()

                # Update learning rate.
                scheduler.step()

                # Calculate actual training step.
                actual_step = accumulate_step_counter // config.accumulation_step

                # log loss
                writer.add_scalar(
                    f'{config.task}-{config.dataset}/Loss',
                    accumulation_loss.item(),
                    actual_step
                )
                mini_batch_iterator.set_description(
                    f'epoch: {epoch}, loss: {accumulation_loss.item():.6f}'
                )

                # Clean up accumulation loss.
                accumulation_loss = 0

                # Clean up gradient.
                optimizer.zero_grad()

                # Save model for each `config.checkpoint_step`.
                if actual_step % config.checkpoint_step == 0:
                    torch.save(
                        model.state_dict(),
                        f'{experiment_path}/{actual_step}.ckpt'
                    )

    writer.flush()
    writer.close()

    # Save the lastest model.
    torch.save(
        model.state_dict(),
        f'{experiment_path}/{actual_step}.ckpt'
    )
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import gc
import numpy as np
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.parallel
import torch.optim
import torch.utils
import torch.utils.data
import torch.utils.tensorboard
from tqdm import tqdm
from transformers import BertConfig, BertModel, BertTokenizer

import dataset
import bert_fine_tune

EX_NO = 0

DATA_PATH = os.path.abspath(
    f'{os.path.abspath(__file__)}/../../data/fine_tune_data'
)
EX_PATH = os.path.abspath(
    f'{os.path.abspath(__file__)}/../../data/fine_tune_experiment/mnli/ex_{EX_NO}'
)

BATCH_SIZE = 32
ACCUMULATION_STEP = 8
EPOCH = 3
LEARNING_RATE = 3e-5
LOG_STEP = 100
SEED = 777

if not os.path.exists(EX_PATH):
    os.makedirs(EX_PATH)

device = torch.device('cpu')

np.random.seed(SEED)
torch.manual_seed(SEED)

if torch.cuda.is_available():
    device = torch.device('cuda:0')
    torch.cuda.manual_seed(SEED)
    torch.cuda.manual_seed_all(SEED)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

config = BertConfig.from_pretrained('bert-base-cased')
tokenizer = BertTokenizer.from_pretrained('bert-base-cased')
model = bert_fine_tune.BertFineTuneModel(in_features=config.hidden_size,
                                         out_features=dataset.MNLI.num_label(),
                                         pretrained_version='bert-base-cased')
model = model.to(device)

train_dataset = dataset.MNLI('train')
collate_fn = dataset.MNLI.create_collate_fn(tokenizer)
train_dataloader = torch.utils.data.DataLoader(train_dataset,
                                               batch_size=BATCH_SIZE // ACCUMULATION_STEP,
                                               collate_fn=collate_fn,
                                               shuffle=True)

writer = torch.utils.tensorboard.SummaryWriter(f'{EX_PATH}/log')

optimizer = torch.optim.AdamW(model.parameters(),
                              lr=LEARNING_RATE)
objective = nn.CrossEntropyLoss()

step_counter = 0
for epoch in range(EPOCH):
    print(f'======EPOCH {epoch}======')
    accumulation_loss = 0
    for (input_ids,
         attention_mask,
         token_type_ids,
         label) in tqdm(train_dataloader):

        optimizer.zero_grad()

        input_ids = input_ids.to(device)
        token_type_ids = token_type_ids.to(device)
        attention_mask = attention_mask.to(device)
        label = label.to(device)

        loss = objective(
            model(
                input_ids=input_ids,
                token_type_ids=token_type_ids,
                attention_mask=attention_mask
            ),
            label
        )

        accumulation_loss += loss / ACCUMULATION_STEP
        step_counter += 1

        if step_counter % ACCUMULATION_STEP == 0:
            accumulation_loss.backward()

            optimizer.step()

            writer.add_scalar('loss',
                              accumulation_loss.item(),
                              step_counter // ACCUMULATION_STEP)

            accumulation_loss.detach()
            del accumulation_loss
            accumulation_loss = 0

        if (step_counter // ACCUMULATION_STEP) % LOG_STEP == 0:
            torch.save(
                model.state_dict(),
                f'{EX_PATH}/checkpoint_{step_counter // ACCUMULATION_STEP}.pt'
            )

        loss.detach()
        input_ids.detach()
        attention_mask.detach()
        token_type_ids.detach()
        label.detach()
        del loss
        del input_ids
        del attention_mask
        del token_type_ids
        del label

        torch.cuda.empty_cache()

writer.close()
torch.save(
    model.state_dict(),
    f'{EX_PATH}/checkpoint_{step_counter // ACCUMULATION_STEP}.pt'
)
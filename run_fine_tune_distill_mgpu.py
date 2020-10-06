#TODO: Rename this file to replace `run_fine_tune_distill.py`
#TODO: Now we specify model to device manuaally,
#It makes that exsistence of `device` property in `config` becomes awkward.
r"""Run fine-tune distillation with multi-GPU.

Usage:
    python run_fine_tune_distill_mgpu.py ...

Run `python run_fine_tune_distill_mgpu.py -h` for help, or see 'doc/fine_tune_*.md'
for more information.
"""

# built-in modules

import argparse
import logging

# my own modules

import fine_tune

# Get main logger.
logger = logging.getLogger('fine_tune.distill')
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO
)

# Filter out message not begin with name 'fine_tune'.
for handler in logging.getLogger().handlers:
    handler.addFilter(logging.Filter('fine_tune'))

if __name__ == "__main__":
    #TODO: Refactor this block.
    # Check GPU device count.
    # If we don't have two GPU device.
    # Then raise ValueError
    fine_tune.util.check_device()

    # Parse arguments from STDIN.
    parser = argparse.ArgumentParser()

    # Required parameters.

    # Shared arguments.
    parser.add_argument(
        '--task',
        help='Name of the distillation task.',
        required=True,
        type=str,
    )
    parser.add_argument(
        '--dataset',
        help=(
            'Name of the distillation dataset generated by previous ' +
            'experiment.'
        ),
        required=True,
        type=str,
    )
    parser.add_argument(
        '--num_class',
        help='Number of classes to classify.',
        required=True,
        type=int,
    )

    # Arguments of teacher model.
    parser.add_argument(
        '--teacher_exp',
        help='Experiment name of the fine-tuned teacher model',
        required=True,
        type=str,
    )
    parser.add_argument(
        '--tmodel',
        help='Name of the teacher model to transfer knowledge',
        required=True,
        type=str,
    )
    parser.add_argument(
        '--tckpt',
        help='Checkpoint of teacher model to generate logits, hidden states and attentions',
        required=True,
        type=int,
    )

    # Arguments of student model.
    parser.add_argument(
        '--experiment',
        help='Name of the current distillation experiment.',
        required=True,
        type=str,
    )
    parser.add_argument(
        '--model',
        help='Name of the model to distill.',
        required=True,
        type=str,
    )
    parser.add_argument(
        '--device_id',
        help='Device ID of student model.',
        required=True,
        type=int,
    )

    # Optional arguments.

    # Shared arguments.
    # parser.add_argument(
    #     '--accum_step',
    #     default=1,
    #     help="Gradient accumulation step. " +
    #     "If not provided will be set as teacher's value",
    #     type=int,
    # )
    # parser.add_argument(
    #     '--amp',
    #     default=False,
    #     help="Use automatic mixed precision during training. " +
    #         "If not provided will be set as teacher's value",
    #     action='store_true'
    # )
    # parser.add_argument(
    #     '--batch_size',
    #     default=32,
    #     help="Distillation batch size. " +
    #         "If not provided will be set as teacher's value",
    #     type=int,
    # )
    # parser.add_argument(
        # '--seed',
        # default=42,
        # help="Control random seed. If not provided will be set as teacher's value",
        # type=int,
    # )

    # Arguments of student model.
    parser.add_argument(
        '--beta1',
        default=0.9,
        help="Optimizer `torch.optim.AdamW`'s beta coefficients.",
        type=float,
    )
    parser.add_argument(
        '--beta2',
        default=0.999,
        help="Optimizer `torch.optim.AdamW`'s beta coefficients.",
        type=float,
    )
    parser.add_argument(
        '--ckpt_step',
        default=1000,
        help='Checkpoint save interval.',
        type=int,
    )
    parser.add_argument(
        '--d_emb',
        default=128,
        help='Embedding dimension.',
        type=int,
    )
    parser.add_argument(
        '--d_ff',
        default=3072,
        help='Transformer layers feed forward dimension.',
        type=int,
    )
    parser.add_argument(
        '--d_model',
        default=768,
        help='Transformer layers hidden dimension.',
        type=int,
    )
    parser.add_argument(
        '--dropout',
        default=0.1,
        help='Dropout probability.',
        type=float,
    )
    parser.add_argument(
        '--eps',
        default=1e-8,
        help="Optimizer `torch.optim.AdamW`'s epsilon.",
        type=float,
    )
    parser.add_argument(
        '--log_step',
        default=500,
        help='Logging interval.',
        type=int,
    )
    parser.add_argument(
        '--lr',
        default=3e-5,
        help="Optimizer `torch.optim.AdamW`'s learning rate.",
        type=float,
    )
    parser.add_argument(
        '--max_norm',
        default=1.0,
        help='Maximum norm of gradient.',
        type=float,
    )
    parser.add_argument(
        '--max_seq_len',
        default=512,
        help='Maximum input sequence length of model input.',
        type=int,
    )
    parser.add_argument(
        '--num_attention_heads',
        default=16,
        help='Number of attention heads in Transformer layers.',
        type=int,
    )
    parser.add_argument(
        '--num_hidden_layers',
        default=6,
        help='Number of Transformer layers.',
        type=int,
    )
    parser.add_argument(
        '--total_step',
        default=50000,
        help='Total number of step to perform training.',
        type=int,
    )
    parser.add_argument(
        '--type_vocab_size',
        default=2,
        help='BERT-like models token type embedding range.',
        type=int,
    )
    parser.add_argument(
        '--warmup_step',
        default=10000,
        help='Linear scheduler warmup step.',
        type=int,
    )
    parser.add_argument(
        '--weight_decay',
        default=0.01,
        help="Optimizer `torch.optim.AdamW` weight decay regularization.",
        type=float,
    )

    # Parse arguments.
    args = parser.parse_args()

    # Load fine-tune teacher model configuration.
    teacher_config = fine_tune.config.TeacherConfig.load(
        experiment=args.teacher_exp,
        model=args.tmodel,
        task=args.task
    )

    # Construct student model configuration.
    student_config = fine_tune.config.StudentConfig(
        accum_step=teacher_config.accum_step,
        amp=teacher_config.amp,
        batch_size=teacher_config.batch_size,
        beta1=args.beta1,
        beta2=args.beta2,
        ckpt_step=args.ckpt_step,
        d_emb=args.d_emb,
        d_ff=args.d_ff,
        d_model=args.d_model,
        dataset=args.dataset,
        dropout=args.dropout,
        eps=args.eps,
        experiment=args.experiment,
        log_step=args.log_step,
        lr=args.lr,
        max_norm=args.max_norm,
        max_seq_len=args.max_seq_len,
        model=args.model,
        num_attention_heads=args.num_attention_heads,
        num_class=args.num_class,
        num_gpu=args.num_gpu,
        num_hidden_layers=args.num_hidden_layers,
        seed=teacher_config.seed,
        task=args.task,
        total_step=args.total_step,
        type_vocab_size=args.type_vocab_size,
        warmup_step=args.warmup_step,
        weight_decay=args.weight_decay,
        device_id=args.device_id
    )

    # Log configuration.
    logger.info(teacher_config)
    logger.info(student_config)

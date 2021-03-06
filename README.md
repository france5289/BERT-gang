# BERT-gang

Using Knowledge Distillation to learn from BERT-like models.
You can see documentation in `doc` for more details.

## Setup

You need `Ubuntu18.04+` and `python3.8+` to run all the code.  
We will use `pipenv` to replace `venv` and `pip`.

- [Pipenv documentation](https://pipenv.pypa.io/en/latest/)

```bash
# clone the project
git clone https://github.com/ProFatXuanAll/BERT-gang

# change to the project directory
cd BERT-gang

# create data folder
mkdir data data/fine_tune

# create virtual environment
pipenv --python 3.8

# install dependencies from `Pipfile`
pipenv install

# activate Pipenv shell and check python version
pipenv shell
python --version
```

## Profiling

- Use `htop` to monitor CPU and memory usage.
  - You need to install `htop` first by `apt-get install htop`.
- Use `nvidia-smi` to monitor GPU and memory usage.
  - You need to install `cuda` driver first.
  - Required `cuda10+`.
- Use `tensorboard --logdir='./data/fine_tune_experiment/log'` to monitor loss, learning rate and accuracy.

## Distillation Result
| Model(Params)     | train acc | dev-m acc | dev-mm acc |
| ----------------- | --------- | --------- | ---------- |
| BERT<sup>base</sup> (110M) | 0.964217  | 0.846052  | 0.850488   |
| Ours( 66M )       | 0.863522  | 0.808864  | 0.811432   |

## Note:
It is a cooperative project with `ProFatXuanAll`, some code is developed by him.

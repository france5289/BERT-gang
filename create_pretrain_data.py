"""Create pretrain data."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import random

from typing import List, Optional

import torch
import transformers


def list_all_files(path: str,
                   ignore_files: List[str] = None
                   ) -> List[str]:
    """List all files in a directory.

    Args:
        path (str):
            Path of a directory which containing pretrain data.
        ignore_files (list[str]):
            Data file names to be not included in the return list.
            Default to None.
    Raises:
        TypeError:
            If `path` is not type `str` or `ignore_files` is not type
            `list(str)`.
        FileNotFoundError:
            If `path` does not exist.
            If files list in `ignore_files` do not exist, then no exception
            will be raised since they were meant to be ignored.
        OSError:
            If `path` is not a directory.
    Returns:
        list[str]:
            Data file names in the given path, sorted by dictionary order.
    """
    # check parameter
    if not isinstance(path, str):
        raise TypeError('parameter `path` must be type `str`.')

    if not os.path.exists(path):
        raise FileNotFoundError(f'directory `{path}` does not exist.')

    if not os.path.isdir(path):
        raise OSError(f'{path} is not a directory.')

    if ignore_files is None:
        ignore_files = []
    else:
        if not isinstance(ignore_files, list):
            raise TypeError(
                'parameter `ignore_files` must be type `list[str]`.')

        for ignore_file in ignore_files:
            if not isinstance(ignore_file, str):
                raise TypeError(
                    'parameter `ignore_files` must be type `list[str]`.')

    all_files = os.listdir(path)
    all_files = sorted(all_files)

    for ignore_file in ignore_files:
        if ignore_file in all_files:
            all_files.remove(ignore_file)

    return all_files


def sample_sentences_from_document(path: str,
                                   n_sample: int = 1
                                   ) -> List[List[str]]:
    """Sample consecutive sentences from a document.

    We assume that input document is formatted as single sentence per line.
    And we will return samples of sentences from input document.
    Each sample consists of 2 consecutive sentences from input document.
    Total return number of samples is equal to `n_sample` if input document is
    big enough, or less than `n_sample` if input document is not big enough.
    We also assume that each sentence of input document is different.
    So no duplicated sample will be returned.

    Args:
        path (str):
            Path of a file which is formatted as single sentence per line,
            and each line is unique.
        n_sample (int, optional):
            Number of samples to sample from input document.
    Raises:
        TypeError:
            If `path` is not type `str` or `n_sample` is not type `int`.
        FileNotFoundError:
            If `path` does not exist.
        OSError:
            If `path` is not a file.
        ValueError:
            If `n_sample` is not a positive integer.
    Returns:
        list[list[str]]:
            List of samples.
            Each sample is a list of string, which consist of 2 consecutive
            sentences from input document.
            If input document is big enough, then return totally `n_sample`
            number of samples, or less than `n_sample` otherwise.
            No duplicated sample will be returned.
    """
    # check parameter
    if not isinstance(path, str):
        raise TypeError('expect parameter `path` to be type `str`.')

    if not os.path.exists(path):
        raise FileNotFoundError(f'file `{path}` does not exist.')

    if not os.path.isfile(path):
        raise OSError(f'{path} is not a file.')

    if not isinstance(n_sample, int):
        raise TypeError('expect parameter `n_sample` to be type `int`.')

    if n_sample <= 0:
        raise ValueError(
            'parameter `n_sample` must be a positive integer.')

    with open(path, 'r') as document:
        # assume input document consist of single sentence per line
        lines = document.read().split('\n')

    sampled_sentence_ids = list(range(len(lines) - 1))
    # case when input document is not big enough
    if len(sampled_sentence_ids) <= n_sample:
        # gather all sentences available and do in place shuffle
        random.shuffle(sampled_sentence_ids)
    # case when input document is big enough
    else:
        sampled_sentence_ids = random.sample(sampled_sentence_ids, n_sample)

    # each sample consist of 2 consecutive sentence
    return [lines[sentence_id:sentence_id + 2] for sentence_id in sampled_sentence_ids]
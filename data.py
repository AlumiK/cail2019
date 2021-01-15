import os
import json
import random

from typing import Sequence


def extract_text_tuples(path: str) -> Sequence:
    """Read data file and extract text tuples."""

    text_tuples = []
    with open(path, 'r', encoding='utf-8') as infile:
        for line in infile:
            line = line.strip()
            items = json.loads(line)
            a = items['A'].replace('\n', '')
            b = items['B'].replace('\n', '')
            c = items['C'].replace('\n', '')

            # `label` is the one more similar to A. We swap B and C if C is more like A.
            if items['label'] == 'C':
                b, c = c, b

            text_tuples.append((a, b, c))
    return text_tuples


def make_input_file(text_tuples: Sequence, path: str, max_len: int, mode: str):
    """Make the input file for BERT."""

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as outfile:
        for a, b, c in text_tuples:

            # Trim A, B and C to about half of `max_len`.
            tokens_a = a[-(max_len // 2):]
            tokens_b = b[-(max_len - max_len // 2):]
            tokens_c = c[-(max_len - max_len // 2):]

            # Concatenate two pieces with `[SEP]` and attach the label at the end.
            line_ab = tokens_a + '[SEP]' + tokens_b + '\t1'
            line_ac = tokens_a + '[SEP]' + tokens_c + '\t0'
            if bool(random.getrandbits(1)):
                outfile.write(line_ab + '\n')
                outfile.write(line_ac + '\n')
            else:
                outfile.write(line_ac + '\n')
                outfile.write(line_ab + '\n')

            # Augment the training dataset.
            # If C(A,B)=1, C(A,C)=0, then C(B,A)=1, C(B,C)=0, C(C,C)=1, C(C,B)=0.
            if mode == 'train':
                line_ba = tokens_b + '[SEP]' + tokens_a + '\t1'
                line_bc = tokens_b + '[SEP]' + tokens_c + '\t0'
                line_cc = tokens_c + '[SEP]' + tokens_c + '\t1'
                line_cb = tokens_c + '[SEP]' + tokens_b + '\t0'
                if bool(random.getrandbits(1)):
                    outfile.write(line_ba + '\n')
                    outfile.write(line_bc + '\n')
                else:
                    outfile.write(line_bc + '\n')
                    outfile.write(line_ba + '\n')
                if bool(random.getrandbits(1)):
                    outfile.write(line_cc + '\n')
                    outfile.write(line_cb + '\n')
                else:
                    outfile.write(line_cb + '\n')
                    outfile.write(line_cc + '\n')

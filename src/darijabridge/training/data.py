"""Data preparation for fine-tuning. Everything except `collate` is plain Python (no torch)."""
import random
from typing import Iterable


def load_pairs(records: Iterable[dict], input_field: str) -> list[tuple[str, str, str]]:
    """(source_text, target_text, source_name) for the records that have both texts."""
    return [(r[input_field], r["text_target"], r["source"]) for r in records
            if r.get(input_field) and r.get("text_target")]


def tokenize_pairs(tokenizer, pairs: list[tuple[str, str, str]], max_length: int,
                   chunk: int = 2000) -> list[tuple[list[int], list[int]]]:
    """Token ids of (input, label). For NLLB the tokenizer adds the language codes: the label starts
    with the target-language token, which is also what `forced_bos_token_id` does at generation time."""
    items = []
    for i in range(0, len(pairs), chunk):
        part = pairs[i:i + chunk]
        enc = tokenizer([p[0] for p in part], text_target=[p[1] for p in part],
                        max_length=max_length, truncation=True)
        items += list(zip(enc["input_ids"], enc["labels"]))
    return items


def length_grouped_batches(lengths: list[int], batch_size: int, seed: int, chunk_factor: int = 50) -> list[list[int]]:
    """Shuffles, then sorts by length inside large chunks so that a batch contains sentences of similar
    length (less padding, faster), and finally shuffles the batches."""
    rng = random.Random(seed)
    order = list(range(len(lengths)))
    rng.shuffle(order)
    batches = []
    size = batch_size * chunk_factor
    for i in range(0, len(order), size):
        chunk = sorted(order[i:i + size], key=lambda j: lengths[j])
        batches += [chunk[k:k + batch_size] for k in range(0, len(chunk), batch_size)]
    rng.shuffle(batches)
    return batches


def longest_first(batches: list[list[int]], items: list[tuple[list[int], list[int]]]) -> list[list[int]]:
    """Moves the batch holding the longest sequence (input or label) to the front. If the GPU is going to
    run out of memory it happens at the very first step, not after an hour of training."""
    if not batches:
        return batches
    def size(batch):
        return max(max(len(items[j][0]), len(items[j][1])) for j in batch)
    k = max(range(len(batches)), key=lambda i: size(batches[i]))
    return [batches[k]] + batches[:k] + batches[k + 1:]


def collate(items: list[tuple[list[int], list[int]]], pad_id: int):
    """Pads inputs with `pad_id` and labels with -100 (ignored by the loss)."""
    import torch

    max_in = max(len(x) for x, _ in items)
    max_lab = max(len(y) for _, y in items)
    input_ids = torch.full((len(items), max_in), pad_id, dtype=torch.long)
    attention = torch.zeros((len(items), max_in), dtype=torch.long)
    labels = torch.full((len(items), max_lab), -100, dtype=torch.long)
    for i, (x, y) in enumerate(items):
        input_ids[i, :len(x)] = torch.tensor(x)
        attention[i, :len(x)] = 1
        labels[i, :len(y)] = torch.tensor(y)
    return {"input_ids": input_ids, "attention_mask": attention, "labels": labels}

from darijabridge.training.data import length_grouped_batches, load_pairs, longest_first


def test_every_index_is_used_once_and_batches_are_bounded():
    lengths = [i % 17 + 1 for i in range(1000)]
    batches = length_grouped_batches(lengths, 16, seed=1)
    flat = [i for b in batches for i in b]
    assert sorted(flat) == list(range(1000)) and max(len(b) for b in batches) <= 16


def test_batches_group_similar_lengths_and_are_reproducible():
    lengths = [(i * 7) % 100 for i in range(2000)]
    batches = length_grouped_batches(lengths, 20, seed=3)
    spread = sum(max(lengths[i] for i in b) - min(lengths[i] for i in b) for b in batches) / len(batches)
    assert spread < 20                                              # random batches would be near 90
    assert batches == length_grouped_batches(lengths, 20, seed=3)
    assert batches != length_grouped_batches(lengths, 20, seed=4)


def test_load_pairs_skips_incomplete_records():
    rows = [{"source": "a", "x": "in", "text_target": "out"}, {"source": "a", "x": "", "text_target": "out"},
            {"source": "b", "x": "in", "text_target": None}]
    assert load_pairs(rows, "x") == [("in", "out", "a")]


def test_longest_batch_goes_first_and_nothing_is_lost():
    items = [([1] * n, [1] * m) for n, m in [(3, 3), (5, 2), (4, 40), (2, 2), (6, 6), (1, 1)]]
    batches = [[0, 1], [2, 3], [4, 5]]                       # the label of item 2 (40 tokens) is the longest
    out = longest_first(batches, items)
    assert out[0] == [2, 3] and sorted(map(tuple, out)) == sorted(map(tuple, batches))
    assert longest_first([], items) == []

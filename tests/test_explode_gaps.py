from background_tasks import explode_gap


def check_gaps(start_slot, end_slot, sprp):
    result = explode_gap(start_slot, end_slot, sprp=sprp)

    assert len(result) > 0

    prev_start = None
    prev_end = None
    for start, end in result:
        assert start < end
        assert start == start_slot or (start == prev_end + 1 and start % sprp == 1)
        assert end == end_slot or (end < end_slot and end % sprp == 0)
        prev_start = start
        prev_end = end


def test_explode_large_gap():
    start_slot = 14273
    end_slot = 7530327
    sprp = 2048
    check_gaps(start_slot, end_slot, sprp)


def test_explode_small_gap_unaligned():
    start_slot = 1
    end_slot = 10
    sprp = 2048
    check_gaps(start_slot, end_slot, sprp)


def test_explode_small_gap_aligned():
    start_slot = 1
    end_slot = 2048
    sprp = 2048
    check_gaps(start_slot, end_slot, sprp)

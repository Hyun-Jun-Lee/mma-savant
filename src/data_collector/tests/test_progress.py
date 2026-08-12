from data_collector.workflows.progress import format_progress


def test_format_progress_overall_only():
    assert format_progress(overall_index=6, overall_total=26) == "[overall 6/26]"


def test_format_progress_batch_item_and_overall():
    assert (
        format_progress(
            batch_index=3,
            batch_total=16,
            item_index=6,
            item_total=20,
            overall_index=46,
            overall_total=312,
        )
        == "[batch 3/16 item 6/20 | overall 46/312]"
    )


def test_format_progress_batch_and_overall():
    assert (
        format_progress(
            batch_index=2,
            batch_total=5,
            overall_index=60,
            overall_total=142,
        )
        == "[batch 2/5 | overall 60/142]"
    )


def test_format_progress_returns_empty_when_no_complete_pairs():
    assert format_progress(batch_index=1, overall_total=10) == ""

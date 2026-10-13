import pytest
from scripts.verify_trained_adapter import accuracy_score


@pytest.mark.parametrize('outcomes,expected', [([False, False], 0.0), ([True, False], 0.5), ([True, True], 1.0)])
def test_accuracy_is_fraction_correct(outcomes, expected):
    assert accuracy_score(outcomes) == expected


def test_empty_evaluation_has_no_accuracy():
    with pytest.raises(ValueError):
        accuracy_score([])


def test_unreviewed_answers_cannot_be_scored():
    with pytest.raises(ValueError):
        accuracy_score([True, None])

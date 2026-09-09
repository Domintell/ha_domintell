"""Tests for legacy shutter status conversion."""

import pytest

from custom_components.domintell.domintell_api.lightprotocol import (
    LpStatus,
    convert_legacy_to_new_gen,
)


@pytest.mark.parametrize(
    ("packed_state", "expected"),
    [
        ("00", [1, 1, 1, 1]),
        ("01", [2, 1, 1, 1]),
        ("02", [3, 1, 1, 1]),
        ("40", [1, 1, 1, 2]),
        ("80", [1, 1, 1, 3]),
        ("24", [1, 2, 3, 1]),
    ],
)
def test_legacy_dtrv_packed_state_conversion(packed_state, expected):
    """Convert packed legacy DTRV states to canonical TypeTrvIo states."""
    status = LpStatus(f"TRV000001O{packed_state}")

    converted = convert_legacy_to_new_gen(status)

    assert converted is not None
    assert len(converted) == 1
    assert converted[0].data == expected
    assert converted[0].is_legacy is False


@pytest.mark.parametrize(
    ("module_type", "packed_state", "expected"),
    [
        ("TRV", "02", [3, 1, 1, 1]),
        ("TPV", "02", [3, 1]),
        ("V24", "02", [3]),
    ],
)
def test_legacy_shutter_modules_share_state_conversion(
    module_type, packed_state, expected
):
    """Apply the legacy shutter conversion to every supported shutter module."""
    status = LpStatus(f"{module_type}000001O{packed_state}")

    converted = convert_legacy_to_new_gen(status)

    assert converted is not None
    assert converted[0].data == expected


def test_newgen_trv_state_is_unchanged():
    """Keep canonical NewGen TypeTrvIo states unchanged."""
    status = LpStatus("TRV/1/6/4/5")

    converted = convert_legacy_to_new_gen(status)

    assert converted == [status]
    assert converted[0].data == [5]
    assert converted[0].is_legacy is False

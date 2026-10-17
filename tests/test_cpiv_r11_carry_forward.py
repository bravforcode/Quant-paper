from __future__ import annotations

import math

import pytest
from research.cpiv import build_demo as demo
from research.cpiv.r11_carry_forward import (
    check_forward_consistency,
    common_map_input_gradient,
    forward_relative_tolerance_for_cpiv,
    synthetic_sensitivity_cases,
)


def test_common_map_spot_and_yield_gradients_match_central_differences() -> None:
    spot, strike, days, rate, yield_ = 100.0, 100.0, 30, 0.03, 0.01
    call_price = demo.bs_price("call", spot, strike, days, rate, yield_, 0.24)
    put_price = demo.bs_price("put", spot, strike, days, rate, yield_, 0.20)
    gradient = common_map_input_gradient(call_price, put_price, spot, strike, days, rate, yield_)

    def cpiv_at(changed_spot: float, changed_yield: float) -> float:
        call_iv = demo.implied_volatility(
            "call", call_price, changed_spot, strike, days, rate, changed_yield
        )
        put_iv = demo.implied_volatility(
            "put", put_price, changed_spot, strike, days, rate, changed_yield
        )
        return 100.0 * (call_iv - put_iv)

    spot_step, yield_step = 1e-4, 1e-6
    spot_fd = (cpiv_at(spot + spot_step, yield_) - cpiv_at(spot - spot_step, yield_)) / (
        2.0 * spot_step
    )
    yield_fd = (cpiv_at(spot, yield_ + yield_step) - cpiv_at(spot, yield_ - yield_step)) / (
        2.0 * yield_step
    )
    assert math.isclose(
        gradient["d_cpiv_pp_d_spot_per_price_unit"], spot_fd, rel_tol=2e-5, abs_tol=1e-6
    )
    assert math.isclose(
        gradient["d_cpiv_pp_d_effective_yield_per_unit"],
        yield_fd,
        rel_tol=2e-5,
        abs_tol=1e-5,
    )


def test_synthetic_carry_and_spot_cases_reproduce_section_73() -> None:
    rows = synthetic_sensitivity_cases()
    carry = {
        row["quote_generation_effective_yield"]: row
        for row in rows
        if row["perturbed_input"].startswith("effective_yield")
    }
    spot = {row["input_delta"]: row for row in rows if row["perturbed_input"] == "inversion_spot"}
    assert math.isclose(carry[0.05]["exact_cpiv_pp"], -3.5872462662525137)
    assert math.isclose(carry[-0.02]["exact_cpiv_pp"], 1.4390309125496603)
    assert math.isclose(carry[0.05]["local_gradient_prediction_pp"], -3.5964639160921905)
    assert math.isclose(spot[0.1]["exact_cpiv_pp"], -0.8743857556008983)
    assert math.isclose(spot[-0.1]["exact_cpiv_pp"], 0.8752612984001984)


def test_forward_consistency_requires_inputs_and_uses_declared_tolerance() -> None:
    spot, rate, yield_, days = 100.0, 0.05, 0.02, 30
    forward = spot * math.exp((rate - yield_) * days / 365.0)
    validated = check_forward_consistency(spot, forward, rate, yield_, days, 1e-12)
    assert validated["status"] == "validated"
    assert math.isclose(validated["effective_yield_implied_by_forward"], yield_)
    inconsistent = check_forward_consistency(spot, forward * 1.01, rate, yield_, days, 1e-4)
    assert inconsistent["status"] == "inconsistent"
    assert check_forward_consistency(None, forward, rate, yield_, days, 1e-4)["status"] == "unknown"
    with pytest.raises(ValueError):
        check_forward_consistency(0.0, forward, rate, yield_, days, 1e-4)


def test_atm_cpiv_tolerance_uses_consistent_forward_units() -> None:
    spot = strike = 100.0
    days, rate, yield_, iv = 30, 0.0, 0.0, 0.20
    call = demo.bs_price("call", spot, strike, days, rate, yield_, iv)
    put = demo.bs_price("put", spot, strike, days, rate, yield_, iv)

    result = forward_relative_tolerance_for_cpiv(
        call, put, spot, strike, days, rate, yield_, cpiv_tolerance_pp=1.0
    )

    assert math.isclose(result["sensitivity_pp_per_basis_point_forward"], 0.08746901103751471)
    assert math.isclose(result["sensitivity_pp_per_one_percent_forward"], 8.746901103751471)
    assert math.isclose(result["forward_relative_tolerance_bp_first_order"], 11.432620400510856)
    assert math.isclose(
        result["forward_relative_tolerance_fraction_first_order"], 0.0011432620400510856
    )
    assert math.isclose(
        result["forward_relative_tolerance_percent_first_order"], 0.11432620400510857
    )
    with pytest.raises(ValueError):
        forward_relative_tolerance_for_cpiv(
            call, put, spot, strike, days, rate, yield_, cpiv_tolerance_pp=-0.1
        )

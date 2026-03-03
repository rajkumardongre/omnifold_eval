"""
Task 3 – Weighted Histogram

A self-contained module that computes and plots a weighted histogram
of a physics observable, with proper √(Σw²) uncertainties.

Usage
-----
    from weighted_histogram import weighted_histogram

    result = weighted_histogram(
        data=df["pT_ll"],
        weights=df["weight_mc"] * df["weights_nominal"],
        bins=30, range=(200, 1500),
        xlabel=r"$p_{T}^{\\ell\\ell}$ [GeV]",
        title="Z boson pT (OmniFold unfolded)",
    )

Run tests
---------
    pytest weighted_histogram.py
    # or
    python weighted_histogram.py
"""

from __future__ import annotations

from typing import Union

import matplotlib.pyplot as plt
import numpy as np


def weighted_histogram(
    data: np.ndarray,
    weights: np.ndarray,
    *,
    bins: Union[int, np.ndarray] = 50,
    range: tuple[float, float] | None = None,
    xlabel: str | None = None,
    ylabel: str = "Weighted events",
    title: str | None = None,
    plot: bool = True,
    ax: plt.Axes | None = None,
    color: str = "#4C72B0",
    show_errors: bool = True,
) -> dict:
    """Compute and optionally plot a weighted histogram.

    Parameters
    ----------
    data : array-like
        Observable values (one per event).
    weights : array-like
        Per-event weights (same length as *data*).
    bins : int or array-like, default 50
        Number of equal-width bins, or explicit bin edges.
    range : (float, float) or None
        Lower and upper range of the bins.  Ignored when *bins* is an
        array of edges.  If None, uses (data.min(), data.max()).
    xlabel, ylabel, title : str or None
        Axis / title labels for the plot.
    plot : bool, default True
        Whether to draw the histogram.
    ax : matplotlib Axes or None
        Axes to draw on.  If None a new figure is created.
    color : str
        Fill colour of the histogram bars.
    show_errors : bool, default True
        Whether to draw √Σw² error bars on each bin.

    Returns
    -------
    dict with keys
        bin_edges    : (n_bins+1,) array of bin edges
        bin_centers  : (n_bins,)   array of bin centres
        bin_contents : (n_bins,)   array - sum of weights per bin
        bin_errors   : (n_bins,)   array - √(Σ w²) per bin
        ax           : the matplotlib Axes (or None if plot=False)
    """
    data = np.asarray(data, dtype=np.float64)
    weights = np.asarray(weights, dtype=np.float64)

    if data.shape != weights.shape:
        raise ValueError(
            f"data and weights must have the same shape, "
            f"got {data.shape} and {weights.shape}"
        )

    # Drop events where either value is non-finite so they don't
    # silently corrupt the histogram.
    mask = np.isfinite(data) & np.isfinite(weights)
    data = data[mask]
    weights = weights[mask]

    bin_contents, bin_edges = np.histogram(
        data, bins=bins, range=range, weights=weights,
    )

    # HEP standard uncertainty: √(Σ wᵢ²) per bin, NOT √(Σ wᵢ).
    # This correctly propagates the variance when events carry
    # non-uniform weights.
    bin_errors_sq, _ = np.histogram(
        data, bins=bin_edges, weights=weights ** 2,
    )
    bin_errors = np.sqrt(bin_errors_sq)

    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])

    result_ax = None
    if plot:
        if ax is None:
            _, ax = plt.subplots(figsize=(8, 5))

        bin_widths = np.diff(bin_edges)
        ax.bar(
            bin_centers, bin_contents,
            width=bin_widths,
            color=color, alpha=0.7,
            edgecolor="black", linewidth=0.5,
            label="Weighted",
        )

        if show_errors:
            ax.errorbar(
                bin_centers, bin_contents,
                yerr=bin_errors,
                fmt="none", ecolor="black",
                elinewidth=1, capsize=2,
            )

        ax.set_xlabel(xlabel or "Observable")
        ax.set_ylabel(ylabel)
        if title:
            ax.set_title(title)
        ax.legend()
        result_ax = ax

    return {
        "bin_edges": bin_edges,
        "bin_centers": bin_centers,
        "bin_contents": bin_contents,
        "bin_errors": bin_errors,
        "ax": result_ax,
    }


# ═══════════════════════════════════════════════════════════════
# Tests
#
# Each test targets a specific behaviour that matters for HEP
# histogramming.  Edge cases are chosen based on the real-world
# properties observed in the OmniFold weight files from Task 1
# (e.g. very small positive weights, possible NaN from failed
# fits, events that should be zeroed out).
# ═══════════════════════════════════════════════════════════════


def test_uniform_weights_match_unweighted():
    """When every weight is 1 the result must equal a plain count histogram.

    This is the most basic sanity check: the weighted path must reduce
    to the unweighted path in the trivial case.
    """
    rng = np.random.default_rng(42)
    data = rng.normal(0, 1, size=10_000)
    weights = np.ones_like(data)

    result = weighted_histogram(data, weights, bins=20, range=(-4, 4), plot=False)
    expected, _ = np.histogram(data, bins=20, range=(-4, 4))

    np.testing.assert_array_almost_equal(result["bin_contents"], expected)


def test_zero_weights_contribute_nothing():
    """Events with weight=0 must not appear in any bin.

    In the OmniFold files, some systematic weight columns are zero for
    non-nominal files (e.g. Sherpa has no ensemble weights).  Zeroed
    events must be invisible.
    """
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    weights = np.array([1.0, 0.0, 1.0, 0.0, 1.0])

    result = weighted_histogram(data, weights, bins=5, range=(0.5, 5.5), plot=False)

    assert result["bin_contents"].sum() == 3.0
    assert result["bin_contents"][1] == 0.0  # event at 2.0 has w=0
    assert result["bin_contents"][3] == 0.0  # event at 4.0 has w=0


def test_negative_weights():
    """Negative weights (common in NLO MC generators) must subtract from
    bin contents, producing a correct net sum.
    """
    data = np.array([1.0, 1.0])
    weights = np.array([5.0, -3.0])

    result = weighted_histogram(data, weights, bins=1, range=(0.5, 1.5), plot=False)

    assert result["bin_contents"][0] == 2.0


def test_errors_are_sqrt_sum_w_squared():
    """Bin uncertainty must be √(Σ wᵢ²), not √(Σ wᵢ).

    This is the critical distinction for weighted histograms in HEP.
    With weights [3, 4, 0] the error is √(9+16+0) = 5, *not* √7.
    """
    data = np.array([1.0, 1.0, 1.0])
    weights = np.array([3.0, 4.0, 0.0])

    result = weighted_histogram(data, weights, bins=1, range=(0.5, 1.5), plot=False)

    expected_error = np.sqrt(3.0**2 + 4.0**2 + 0.0**2)  # = 5.0
    np.testing.assert_almost_equal(result["bin_errors"][0], expected_error)


def test_mismatched_shapes_raise():
    """data and weights with different shapes must raise ValueError.

    This catches the common mistake of passing a weight array from one
    file alongside observables from another (different event counts).
    """
    try:
        weighted_histogram(np.array([1, 2, 3]), np.array([1, 2]), plot=False)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_nan_and_inf_are_filtered():
    """NaN/Inf in data or weights must be silently dropped.

    NaN can appear if a weight column is read from a file where the
    value was not computed (e.g. a failed fit).  These events must not
    corrupt the histogram.
    """
    data = np.array([1.0, np.nan, 3.0, 4.0, np.inf])
    weights = np.array([1.0, 1.0, np.nan, 1.0, 1.0])

    result = weighted_histogram(data, weights, bins=5, range=(0.5, 5.5), plot=False)

    # Only (1.0, w=1.0) and (4.0, w=1.0) survive the filter
    assert result["bin_contents"].sum() == 2.0


def test_empty_input():
    """Empty arrays must produce a valid histogram with all-zero bins.

    This can happen after a tight selection leaves no events.
    """
    result = weighted_histogram(
        np.array([]), np.array([]), bins=10, range=(0, 1), plot=False,
    )

    assert result["bin_contents"].sum() == 0.0
    assert len(result["bin_edges"]) == 11
    assert len(result["bin_errors"]) == 10


def test_single_bin():
    """Single-bin histogram must sum all weights into one bin."""
    data = np.array([1.0, 2.0, 3.0])
    weights = np.array([0.5, 1.5, 2.0])

    result = weighted_histogram(data, weights, bins=1, range=(0.5, 3.5), plot=False)

    assert result["bin_contents"][0] == 4.0
    assert len(result["bin_edges"]) == 2


def test_explicit_bin_edges():
    """When bins is an array of edges, those edges must be used as-is.

    This is important for non-uniform binning, which is common in HEP
    when the observable spans several orders of magnitude (e.g. pT).
    """
    data = np.array([1.0, 2.0, 3.0, 4.0])
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    edges = np.array([0.0, 2.5, 5.0])

    result = weighted_histogram(data, weights, bins=edges, plot=False)

    assert len(result["bin_contents"]) == 2
    assert result["bin_contents"][0] == 2.0  # events at 1, 2
    assert result["bin_contents"][1] == 2.0  # events at 3, 4
    np.testing.assert_array_equal(result["bin_edges"], edges)


def test_plot_returns_axes():
    """When plot=True the returned dict must contain a matplotlib Axes."""
    data = np.array([1.0, 2.0, 3.0])
    weights = np.array([1.0, 1.0, 1.0])

    result = weighted_histogram(data, weights, bins=3, range=(0.5, 3.5), plot=True)

    assert result["ax"] is not None
    plt.close("all")


def test_plot_false_returns_no_axes():
    """When plot=False the returned ax must be None."""
    data = np.array([1.0, 2.0])
    weights = np.array([1.0, 1.0])

    result = weighted_histogram(data, weights, bins=2, range=(0.5, 2.5), plot=False)

    assert result["ax"] is None


# ── Run all tests when executed directly ──────────────────────

def _run_tests():
    test_uniform_weights_match_unweighted()
    test_zero_weights_contribute_nothing()
    test_negative_weights()
    test_errors_are_sqrt_sum_w_squared()
    test_mismatched_shapes_raise()
    test_nan_and_inf_are_filtered()
    test_empty_input()
    test_single_bin()
    test_explicit_bin_edges()
    test_plot_returns_axes()
    test_plot_false_returns_no_axes()
    print("All 11 tests passed.\n")


def _demo():
    """Load the nominal OmniFold file and plot four key observables."""
    import os
    import pandas as pd

    DATA_PATH = os.path.join("files", "pseudodata", "multifold.h5")
    if not os.path.isfile(DATA_PATH):
        print(f"Demo skipped - {DATA_PATH} not found.")
        return

    print(f"Loading {DATA_PATH} …")
    df = pd.read_hdf(DATA_PATH, key="df")
    w = (df["weight_mc"] * df["weights_nominal"]).values
    print(f"  {len(df):,} events loaded.\n")

    observables = [
        ("pT_ll",        r"$p_{\mathrm{T}}^{\ell\ell}$ [GeV]",  (200, 1500),   40),
        ("eta_l1",       r"$\eta_{\ell_1}$",                     (-2.5, 2.5),   50),
        ("m_trackj1",    r"$m_{\mathrm{jet\,1}}$ [GeV]",         (0, 80),       40),
        ("tau1_trackj1", r"$\tau_1^{\mathrm{jet\,1}}$",          (0, 0.6),      30),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "OmniFold Weighted Histograms - Nominal (MG5)",
        fontsize=14, fontweight="bold", y=0.98,
    )

    for ax, (col, label, rng, nbins) in zip(axes.flat, observables):
        weighted_histogram(
            data=df[col].values,
            weights=w,
            bins=nbins,
            range=rng,
            xlabel=label,
            ylabel="Weighted events",
            ax=ax,
        )
        ax.set_title(col)

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    out = "weighted_histograms_demo.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    print(f"Saved {out}")
    plt.show()


if __name__ == "__main__":
    _run_tests()
    _demo()
"""Histogram plots for raw or pre-binned data."""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from .base import BasePlot
from .style import set_plot_style


def _as_1d(values, name: str) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    return array


def _prepare_histogram(
    data=None,
    *,
    bins=None,
    values=None,
    weights=None,
    errors=None,
    sqrt_n: bool = False,
):
    """Return ``(edges, bin_values, bin_errors)`` for a histogram input."""
    if (data is None) == (values is None):
        raise ValueError("Provide exactly one of data or values")
    if errors is not None and sqrt_n:
        raise ValueError("Provide errors or sqrt_n=True, not both")

    if data is not None:
        data = _as_1d(data, "data")
        if weights is not None:
            weights = _as_1d(weights, "weights")
            if weights.size != data.size:
                raise ValueError("weights and data must have the same length")
        if bins is None:
            bin_values, edges = np.histogram(data, weights=weights)
        else:
            bin_values, edges = np.histogram(data, bins=bins, weights=weights)

        if errors is not None:
            bin_errors = _as_1d(errors, "errors")
        elif sqrt_n:
            counts, _ = np.histogram(data, bins=edges)
            bin_errors = np.sqrt(counts)
        elif weights is not None:
            weight_squared, _ = np.histogram(data, bins=edges, weights=weights**2)
            bin_errors = np.sqrt(weight_squared)
        else:
            bin_errors = None
    else:
        bin_values = _as_1d(values, "values")
        edges = _as_1d(bins, "bins")
        if edges.size != bin_values.size + 1:
            raise ValueError("bins must contain exactly one more entry than values")
        if np.any(np.diff(edges) <= 0):
            raise ValueError("bins must be strictly increasing")
        if errors is not None:
            bin_errors = _as_1d(errors, "errors")
        elif sqrt_n:
            bin_errors = np.sqrt(np.maximum(bin_values, 0))
        else:
            bin_errors = None

    if bin_errors is not None and bin_errors.size != bin_values.size:
        raise ValueError("errors must have one entry per bin")
    if bin_errors is not None and np.any(bin_errors < 0):
        raise ValueError("errors must be non-negative")

    return edges, bin_values, bin_errors


class Histogram(BasePlot):
    """Plot one histogram from raw data or pre-binned values.

    Raw-data example::

        plot = Histogram(data, bins=50, sqrt_n=True)

    Pre-binned example::

        plot = Histogram(values=counts, bins=edges, errors=uncertainties)

    If raw data are weighted and no error option is supplied, errors are
    computed as ``sqrt(sum(weights**2))`` in each bin.
    """

    def __init__(
        self,
        data=None,
        *,
        bins=None,
        values=None,
        weights=None,
        errors=None,
        sqrt_n: bool = False,
        ax=None,
        label=None,
        color=None,
        **kwargs,
    ):
        super().__init__(ax=ax, **kwargs)
        self.bins, self.values, self.errors = _prepare_histogram(
            data,
            bins=bins,
            values=values,
            weights=weights,
            errors=errors,
            sqrt_n=sqrt_n,
        )
        self.bin_centers = 0.5 * (self.bins[:-1] + self.bins[1:])
        self.color = color or self.colours[0]
        self.label = label
        self.draw()

    def draw(self):
        """Draw the histogram and return its line and error-bar artists."""
        line = self.ax.stairs(
            self.values, self.bins, label=self.label, color=self.color
        )
        errorbar = None
        if self.errors is not None:
            errorbar = self.ax.errorbar(
                self.bin_centers,
                self.values,
                yerr=self.errors,
                fmt="none",
                capsize=2,
                ecolor=self.color,
            )
        if self.label is not None:
            self.ax.legend()
        return line, errorbar


class HistogramComparison(BasePlot):
    """Plot two histograms with a residual-significance panel below.

    The residual is ``(values1 - values2) / sqrt(errors1**2 + errors2**2)``.
    Each series accepts the same raw-data or pre-binned arguments as
    :class:`Histogram`.
    """

    def __init__(
        self,
        data1=None,
        data2=None,
        *,
        bins=None,
        values1=None,
        values2=None,
        weights1=None,
        weights2=None,
        errors1=None,
        errors2=None,
        sqrt_n1: bool = False,
        sqrt_n2: bool = False,
        labels=("series 1", "series 2"),
        colors=None,
        figsize=(8, 7),
        ax=None,
        residual_ax=None,
        **kwargs,
    ):
        set_plot_style()
        if ax is None and residual_ax is None:
            self.fig, (self.ax, self.residual_ax) = plt.subplots(
                2,
                1,
                sharex=True,
                figsize=figsize,
                gridspec_kw={"height_ratios": [3, 1], "hspace": 0.05},
                **kwargs,
            )
        elif ax is not None and residual_ax is not None:
            self.ax = ax
            self.residual_ax = residual_ax
            self.fig = ax.figure
        else:
            raise ValueError("Provide both ax and residual_ax, or neither")

        self.colours = plt.rcParams["axes.prop_cycle"].by_key()["color"]
        colors = colors or (self.colours[0], self.colours[1])
        if len(colors) != 2:
            raise ValueError("colors must contain exactly two colors")
        if len(labels) != 2:
            raise ValueError("labels must contain exactly two labels")

        self.bins1, self.values1, self.errors1 = _prepare_histogram(
            data1,
            bins=bins,
            values=values1,
            weights=weights1,
            errors=errors1,
            sqrt_n=sqrt_n1,
        )
        self.bins2, self.values2, self.errors2 = _prepare_histogram(
            data2,
            bins=bins,
            values=values2,
            weights=weights2,
            errors=errors2,
            sqrt_n=sqrt_n2,
        )
        if not np.array_equal(self.bins1, self.bins2):
            raise ValueError("Both series must use identical bin edges")
        if self.errors1 is None or self.errors2 is None:
            raise ValueError("Comparison plots require errors for both series")

        self.bins = self.bins1
        self.bin_centers = 0.5 * (self.bins[:-1] + self.bins[1:])
        self.labels = labels
        self.colors = colors
        self.combined_errors = np.sqrt(self.errors1**2 + self.errors2**2)
        self.residuals = np.divide(
            self.values1 - self.values2,
            self.combined_errors,
            out=np.full(self.combined_errors.shape, np.nan, dtype=float),
            where=self.combined_errors > 0,
        )
        self.draw()

    def draw(self):
        """Draw both series and the residual-significance panel."""
        for values, errors, label, color in zip(
            (self.values1, self.values2),
            (self.errors1, self.errors2),
            self.labels,
            self.colors,
        ):
            self.ax.stairs(values, self.bins, label=label, color=color)
            self.ax.errorbar(
                self.bin_centers,
                values,
                yerr=errors,
                fmt="none",
                capsize=2,
                ecolor=color,
            )

        valid = np.isfinite(self.residuals)
        self.residual_ax.axhline(0, color="black", linestyle="--", linewidth=1)
        self.residual_ax.errorbar(
            self.bin_centers[valid],
            self.residuals[valid],
            yerr=np.ones(np.count_nonzero(valid)),
            fmt="o",
            markersize=3,
            color="black",
            ecolor="gray",
            capsize=2,
        )
        self.ax.set_yscale("log")
        self.ax.set_ylabel("Counts")
        self.residual_ax.set_xlabel("Bin value")
        self.residual_ax.set_ylabel("Residuals")
        self.ax.legend()
        return self.fig, (self.ax, self.residual_ax)


TwoSeriesHistogram = HistogramComparison
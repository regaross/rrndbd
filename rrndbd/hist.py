"""Histogram plots for raw or pre-binned data."""

from __future__ import annotations

from dataclasses import dataclass

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


def _fill_histogram_band(ax, bins, values, errors, color, alpha=0.25):
    """Fill a stepwise band from ``values - errors`` to ``values + errors``."""
    positive = values[values > 0]
    floor = 1e-2 * positive.min() if positive.size else 1e-6
    lower = np.maximum(values - errors, floor)
    upper = values + errors
    return ax.fill_between(
        bins,
        np.r_[lower, lower[-1]],
        np.r_[upper, upper[-1]],
        step="post",
        color=color,
        alpha=alpha,
        linewidth=0,
        zorder=1,
    )


def _remove_errorbar(errorbar):
    """Remove a matplotlib ErrorbarContainer if one was drawn."""
    if errorbar is not None:
        errorbar.remove()


def _remove_artist(artist):
    """Remove a matplotlib artist if one was drawn."""
    if artist is not None:
        artist.remove()


@dataclass
class _HistogramSeries:
    values: np.ndarray
    errors: np.ndarray | None
    color: object
    label: str | None = None
    line: object = None
    errorbar: object = None
    error_band: object = None


def _remove_series_artists(spec: _HistogramSeries):
    """Remove every artist belonging to one histogram series."""
    _remove_artist(spec.line)
    _remove_errorbar(spec.errorbar)
    _remove_artist(spec.error_band)
    spec.line = None
    spec.errorbar = None
    spec.error_band = None


def _draw_series(
    ax,
    bins,
    bin_centers,
    spec: _HistogramSeries,
    *,
    alpha=1.0,
    use_error_bands=False,
    band_alpha=0.25,
):
    """Draw stairs plus error bars or an error band for one series."""
    spec.line = ax.stairs(
        spec.values,
        bins,
        label=spec.label,
        color=spec.color,
        alpha=alpha,
        zorder=2,
    )
    spec.errorbar = None
    spec.error_band = None
    if spec.errors is None:
        return spec
    if use_error_bands:
        spec.error_band = _fill_histogram_band(
            ax, bins, spec.values, spec.errors, spec.color, band_alpha
        )
    else:
        spec.errorbar = ax.errorbar(
            bin_centers,
            spec.values,
            yerr=spec.errors,
            fmt="none",
            capsize=2,
            ecolor=spec.color,
        )
    return spec


class Histogram(BasePlot):
    """Plot one or more histograms from raw data or pre-binned values.

    Raw-data example::

        plot = Histogram(data, bins=50, sqrt_n=True)

    Pre-binned example::

        plot = Histogram(values=counts, bins=edges, errors=uncertainties)

    Add further series after construction; they reuse the same bins and
    pick the next color unless ``color`` is given::

        plot.add(data_b, sqrt_n=True, label="B")

    An empty plot with bins preset is also allowed::

        plot = Histogram(bins=edges)
        plot.add(data_a, sqrt_n=True, label="A")

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
        self.series = []
        self.bins = None
        self.bin_centers = None
        self._bin_spec = bins
        self.alpha = 1.0
        self._use_error_bands = False
        self._error_band_alpha = 0.25
        self._store_bin_edges(bins)

        has_series = data is not None or values is not None
        if has_series:
            self.add(
                data,
                bins=bins,
                values=values,
                weights=weights,
                errors=errors,
                sqrt_n=sqrt_n,
                label=label,
                color=color,
            )

    def _store_bin_edges(self, bins):
        """Record ``bins``; store edges now if they already look like edges."""
        self._bin_spec = bins
        if bins is None:
            return
        array = np.asarray(bins, dtype=float)
        if array.ndim == 1 and array.size >= 2 and np.all(np.diff(array) > 0):
            self.bins = array
            self.bin_centers = 0.5 * (array[:-1] + array[1:])

    def _first_series(self) -> _HistogramSeries:
        if not self.series:
            raise ValueError("Histogram has no series yet")
        return self.series[0]

    @property
    def values(self):
        return self._first_series().values

    @property
    def errors(self):
        return self._first_series().errors

    @property
    def color(self):
        return self._first_series().color

    @color.setter
    def color(self, color):
        self._first_series().color = color

    @property
    def label(self):
        return self._first_series().label

    @label.setter
    def label(self, label):
        self._first_series().label = label

    def add(
        self,
        data=None,
        *,
        bins=None,
        values=None,
        weights=None,
        errors=None,
        sqrt_n: bool = False,
        label=None,
        color=None,
    ):
        """Add a series, draw it, and return ``self`` for chaining."""
        if bins is not None:
            prepare_bins = bins
        elif self.bins is not None:
            prepare_bins = self.bins
        else:
            prepare_bins = self._bin_spec
        edges, bin_values, bin_errors = _prepare_histogram(
            data,
            bins=prepare_bins,
            values=values,
            weights=weights,
            errors=errors,
            sqrt_n=sqrt_n,
        )
        if self.bins is None:
            self.bins = edges
            self.bin_centers = 0.5 * (edges[:-1] + edges[1:])
        elif not np.array_equal(edges, self.bins):
            raise ValueError("All series must use identical bin edges")

        spec = _HistogramSeries(
            values=bin_values,
            errors=bin_errors,
            color=color or self.colours[len(self.series) % len(self.colours)],
            label=label,
        )
        _draw_series(
            self.ax,
            self.bins,
            self.bin_centers,
            spec,
            alpha=self.alpha,
            use_error_bands=self._use_error_bands,
            band_alpha=self._error_band_alpha,
        )
        self.series.append(spec)
        if spec.label is not None:
            self.ax.legend()
        return self

    def error_bands(self, alpha=0.25):
        """Replace error bars with a pale histogram-shaped uncertainty band."""
        if not self.series or all(spec.errors is None for spec in self.series):
            raise ValueError("Cannot draw an error band without errors")
        self._use_error_bands = True
        self._error_band_alpha = alpha
        bands = []
        for spec in self.series:
            if spec.errors is None:
                continue
            if spec.error_band is not None:
                bands.append(spec.error_band)
                continue
            _remove_errorbar(spec.errorbar)
            spec.errorbar = None
            spec.error_band = _fill_histogram_band(
                self.ax, self.bins, spec.values, spec.errors, spec.color, alpha
            )
            bands.append(spec.error_band)
        return bands

    draw_error_band = error_bands

    def draw(self):
        """Redraw every series and return a list of ``(line, errorbar)`` pairs."""
        for spec in self.series:
            _remove_series_artists(spec)
            _draw_series(
                self.ax,
                self.bins,
                self.bin_centers,
                spec,
                alpha=self.alpha,
                use_error_bands=self._use_error_bands,
                band_alpha=self._error_band_alpha,
            )
        if any(spec.label is not None for spec in self.series):
            self.ax.legend()
        return [(spec.line, spec.errorbar) for spec in self.series]


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
        self.alpha = 0.75
        self.combined_errors = np.sqrt(self.errors1**2 + self.errors2**2)
        self.residuals = np.divide(
            self.values1 - self.values2,
            self.combined_errors,
            out=np.full(self.combined_errors.shape, np.nan, dtype=float),
            where=self.combined_errors > 0,
        )
        self._error_bands = None
        self.draw()

    def error_bands(self, alpha=0.25):
        """Fill a pale histogram-shaped band between the error bars."""
        if self.errors1 is None or self.errors2 is None:
            raise ValueError("Cannot draw an error band without errors")
        if self._error_bands is not None:
            return self._error_bands
        self._error_bands = [
            _fill_histogram_band(self.ax, self.bins, values, errors, color, alpha)
            for values, errors, color in zip(
                (self.values1, self.values2),
                (self.errors1, self.errors2),
                self.colors,
            )
        ]
        return self._error_bands

    draw_error_band = error_bands

    def draw(self):
        """Draw both series and the residual-significance panel."""
        self._error_bands = None
        for values, label, color in zip(
            (self.values1, self.values2),
            self.labels,
            self.colors,
        ):
            self.ax.stairs(
                values,
                self.bins,
                label=label,
                color=color,
                alpha=self.alpha,
                zorder=2,
            )
        self.error_bands()

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

    def set_labels(self, xlabel=None, ylabel=None, title=None):
        if xlabel:
            self.residual_ax.set_xlabel(xlabel)
        if ylabel:
            self.ax.set_ylabel(ylabel)
        if title:
            self.ax.set_title(title)


class HistogramOverlay(Histogram):
    """Overlay several histograms on one axes.

    Each series is a dict accepted by :func:`_prepare_histogram`, plus optional
    ``label`` and ``color`` keys. All series share the same ``bins``.
    """

    def __init__(self, series, *, bins=None, ax=None, **kwargs):
        if not series:
            raise ValueError("Provide at least one series")
        super().__init__(bins=bins, ax=ax, **kwargs)
        for spec in series:
            spec = dict(spec)
            label = spec.pop("label", None)
            color = spec.pop("color", None)
            self.add(label=label, color=color, **spec)


TwoSeriesHistogram = HistogramComparison
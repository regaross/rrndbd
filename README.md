# rrndbd

**R**egan **R**oss's **N**eutrinoless **D**ouble **B**eta **D**ecay plotting and calculation library.

A Python package for creating publication-quality visualizations and performing calculations related to neutrinoless double beta decay (0νββ) research, with a focus on xenon-based experiments and nuclear fission products.

## Overview

`rrndbd` provides a collection of specialized plotting classes and utilities for visualizing:

- Neutrino mass hierarchies and orderings
- Effective Majorana mass constraints (the "lobster plot")
- Xenon-based double beta decay experiments
- Nuclear isobars and mass excesses
- Fission product yields and binding energies
- Atmospheric gas compositions and xenon isotopes
- Beta decay spectra (e.g., tritium)

The package is built on top of matplotlib with custom base classes that provide consistent styling and simplified interfaces.

## Features

- 🎨 **Consistent styling**: All plots use a unified matplotlib style configuration
- 🔧 **Extensible base classes**: `BasePlot` and `TwoPanelBasePlot` for easy customization
- 📊 **Ready-to-use plot types**: Each major plot type is encapsulated in its own module
- 📈 **Publication-ready**: High-quality figures suitable for papers and presentations
- 🧮 **Physics calculations**: Built-in support for neutrino mass calculations and PMNS matrix operations
- 🗂️ **Data-driven**: Works with CSV data files for nuclear physics data

## Installation

### Using Conda (Recommended)

Clone the repository and create the environment:

```bash
git clone https://github.com/regaross/rrndbd.git
cd rrndbd
conda env create -f environment.yml
conda activate rrndbd
```

### Dependencies

- Python 3.13+
- matplotlib
- numpy
- pandas
- scipy
- pyyaml
- pdg

## Quick Start

### The Lobster Plot 🦞

The "lobster plot" shows the effective Majorana neutrino mass (⟨m<sub>ββ</sub>⟩) as a function of the lightest neutrino mass eigenstate, displaying both normal and inverted mass orderings:

```python
from rrndbd.lobster import LobsterPlot

plot = LobsterPlot()
plot.show()
```

This creates a plot showing:
- **Normal ordering**: Two close small mass eigenstates with one larger separated mass
- **Inverted ordering**: Two close large mass eigenstates with one smaller separated mass

Experimental constraints can be added by modifying the [`nu_mass_constraints.yml`](rrndbd/data/nu_mass_constraints.yml) file.

### Neutrino Mass Orderings

Visualize the decomposition of neutrino mass eigenstates into flavor components:

```python
from rrndbd.orderings import OrderingPlot

plot = OrderingPlot()
plot.show()
```

### Isobar Plot (A=136)

Demonstrate why Xe-136 undergoes double beta decay by showing the A=136 isobar chain:

```python
from rrndbd.isobars import IsobarsPlot

plot = IsobarsPlot()
plot.show()
```

### Xenon Experiments Over Time

Motivate the search for new xenon sources by plotting historical and planned experiments:

```python
from rrndbd.xe_experiments import XeExperimentPlot

plot = XeExperimentPlot()
plot.show()
```

### Fission Product Yields

Visualize nuclear fission products and binding energy curves:

```python
from rrndbd.fission_yields import FissionYieldPlot

plot = FissionYieldPlot(show_be=True)
plot.show()
```

### Atmospheric Gases and Xenon Isotopes

Two-panel plot showing atmospheric gas composition and natural xenon isotope abundances:

```python
from rrndbd.gases import AtmosXePlot

plot = AtmosXePlot()
# Automatically displays both panels
```

### Tritium Beta Decay Spectrum

Plot the beta decay spectrum of tritium:

```python
from rrndbd.beta import TritiumBetaPlot

plot = TritiumBetaPlot()
plot.show()
```

## Architecture

### Base Classes

The package provides two fundamental base classes in `rrndbd/base.py`:

#### `BasePlot`

A base class for single-panel plots with common functionality:

```python
from rrndbd.base import BasePlot

class MyCustomPlot(BasePlot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Your plotting code here
        self.set_labels('X Label', 'Y Label', 'Title')
        self.show()
```

**Methods:**
- `set_labels(xlabel, ylabel, title)`: Set axis labels and title
- `show()`: Display the plot
- `save(filename)`: Save the figure
- `logscalexy()`: Set both axes to log scale

#### `TwoPanelBasePlot`

A base class for side-by-side two-panel plots:

```python
from rrndbd.base import TwoPanelBasePlot

class MyTwoPanelPlot(TwoPanelBasePlot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Access panels via self.ax1 and self.ax2
        self.show()
```

### Module Structure

Each plot type is organized into its own module:

- `base.py` - Base plotting classes
- `lobster.py` - Lobster plot (effective Majorana mass)
- `orderings.py` - Neutrino mass ordering visualizations
- `isobars.py` - Nuclear isobar plots
- `xe_experiments.py` - Xenon experiment timeline
- `fission_yields.py` - Fission product yields
- `gases.py` - Atmospheric gas and xenon isotope plots
- `beta.py` - Beta decay spectra
- `constants.py` - Physical constants and neutrino parameters
- `style.py` - Matplotlib style configuration
- `oscillations.py` - (Planned) Neutrino oscillation experiments

## Data Files

The package includes several CSV data files in `rrndbd/data/`:

- `nu_mass_constraints.yml` - Experimental constraints on neutrino masses
- `fission_yields.csv` - Nuclear fission product data
- `isobars136.csv` - Mass excess data for A=136 isobars
- `xenon_experiments.csv` - Historical and planned xenon experiments
- `xenon_isotopes.csv` - Natural xenon isotope abundances
- `atmosgas.csv` - Atmospheric gas composition

## Customization

### Custom Styling

The package uses a custom matplotlib style. Modify `rrndbd/style.py` to adjust:
- Color schemes
- Font sizes
- Line widths
- Figure dimensions

### Adding New Plot Types

1. Create a new module in `rrndbd/`
2. Inherit from `BasePlot` or `TwoPanelBasePlot`
3. Implement your visualization in `__init__`
4. Make the file executable if desired: `chmod +x rrndbd/your_plot.py`
5. Import in `rrndbd/__init__.py` to expose it at the package level

## Executable Modules

Individual plot modules are designed to be executable for quick demonstrations:

```bash
python -m rrndbd.lobster
python -m rrndbd.isobars
# etc.
```

## Use Cases

This library is particularly useful for:

- 📝 **Thesis and dissertation work** in neutrino physics
- 📄 **Research publications** requiring standardized figures
- 🎤 **Conference presentations** on 0νββ decay
- 🎓 **Educational materials** on neutrino mass and nuclear physics
- 🔬 **Experimental planning** for xenon-based detectors

## Future Development

Planned additions include:

- Neutrino oscillation experiment visualizations (`oscillations.py`)
- Xenon gas yield predictions from used nuclear fuel
- Additional experimental constraint overlays
- Interactive plotting capabilities

## Contributing

This repository serves as a centralized collection of plotting scripts for thesis work. Contributions, suggestions, and bug reports are welcome via GitHub issues.

## Author

Regan Ross ([@regaross](https://github.com/regaross))

---

**Repository**: [https://github.com/regaross/rrndbd](https://github.com/regaross/rrndbd)
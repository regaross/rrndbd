import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Patch
from .base import BasePlot
from .constants import fetch_neutrino_constants, pmns
from .lobster import neutrino_masses # returns m1, m2, m3
from .constants import ELECTRON_MASS_MEV

_NEUTRINO_CONSTANTS = fetch_neutrino_constants()
_PMNS = pmns()
DSM21 = (_NEUTRINO_CONSTANTS['dsm21']['value'], _NEUTRINO_CONSTANTS['dsm21']['error'])
DSM32 = (_NEUTRINO_CONSTANTS['dsm32']['value'], _NEUTRINO_CONSTANTS['dsm32']['error'])
SST12 = (_NEUTRINO_CONSTANTS['sst12']['value'], _NEUTRINO_CONSTANTS['sst12']['error'])
SST13 = (_NEUTRINO_CONSTANTS['sst13']['value'], _NEUTRINO_CONSTANTS['sst13']['error'])
SST23 = (_NEUTRINO_CONSTANTS['sst23']['value'], _NEUTRINO_CONSTANTS['sst23']['error'])
DCP =   (_NEUTRINO_CONSTANTS['dcp']['value'],   _NEUTRINO_CONSTANTS['dcp']['error'])

class OrderingPlot(BasePlot):
    """
    A plot of the neutrino mass orderings showing the decomposition of the
    mass eigenstates into their flavour components.
    """

    def __init__(self, squared=False, **kwargs):
        # Initialize base class with two vertically stacked, shared-x subplots
        super().__init__(nrows=2, sharex=True, gridspec_kw={'hspace': 0}, **kwargs)

        # Convenience handles for axes
        self.top, self.bot = self.ax

        # Compute mass eigenvalues for both orderings
        norm_masses = neutrino_masses(0)
        inv_masses = neutrino_masses(0, True, True)
        inv_order = [3, 1, 2]

        # Determine whether to square the mass scale
        self.pow = 2 if squared else 1

        # Layout parameters
        self.xscale = 100
        self.xoffset = 0.15 * self.xscale
        self.width = 0.25 * self.xscale
        self.ax[0].set_xlim(0, self.xscale)

        # Custom categorical tick positions (no default numeric ticks)
        custom_ticks = [27.5, 72.5]
        self.bot.set_xticks(custom_ticks)
        self.top.tick_params(bottom = False)
        self.bot.set_xticklabels(['Normal Ordering', 'Inverted Ordering'])

        if squared:
            self.fig.supylabel(r"Neutrino Squared Mass [eV$^2$]", x=0.01)  # adjust x if needed
        else:
            self.fig.supylabel("Neutrino Mass [eV]", x=0.01)  # adjust x if needed

        # Add vertical gridlines for reference
        for ax in (self.top, self.bot):
            ax.grid(axis='x')

        # Define y-ranges so the heavier and lighter mass states are separated visually
        # --- Upper panel (heavier states)
        self.toprange = (
            inv_masses[1] ** self.pow * 0.95,
            inv_masses[2] ** self.pow * 1.05,
        )
        self.top.set_ylim(*self.toprange)

        # --- Lower panel (lighter states)
        self.botrange = (
            -(norm_masses[1] ** self.pow) * 0.25,
            (norm_masses[1] ** self.pow) * 1.25,
        )
        self.bot.set_ylim(*self.botrange)
        self.botheight = self.botrange[1] / 15

        # Draw mass bars for normal ordering (left)
        for i, m in enumerate(norm_masses):
            self.add_mass_bar(
                m_state=i + 1,
                x=self.xoffset,
                y=m ** self.pow,
                top=(i > 1),
            )

        # Draw mass bars for inverted ordering (right)
        for i, m in enumerate(inv_masses):
            self.add_mass_bar(
                m_state=inv_order[i],
                x=self.xscale - self.xoffset - self.width,
                y=m ** self.pow,
                top=(i > 0),
            )

        self.add_flavour_legend()

    # ---------------------------------------------------------------------

    def add_mass_bar(self, m_state=1, x=0.0, y=0.0, top=False, height_factor=15):
        """
        Draws a tri-coloured bar representing the flavour decomposition
        of a given mass eigenstate (m1, m2, m3).
        """

        # Choose axis and vertical scaling based on which panel we're in
        if top:
            this_height = (self.toprange[1] - self.toprange[0]) / height_factor
            this_ax = self.top
        else:
            this_height = (self.botrange[1] - self.botrange[0]) / height_factor
            this_ax = self.bot

        # Construct flavour-state vector and compute decomposition
        m = np.zeros(3, dtype=int)
        m[m_state - 1] = 1
        md = np.abs(_PMNS @ m) ** 2  # |U|^2 decomposition

        # Draw each flavour segment
        start_x = x
        for i, eig in enumerate(md):
            this_width = eig * self.width
            this_rec = Rectangle(
                (start_x, y),
                width=this_width,
                height=this_height,
                color=self.colours[i],
            )
            this_ax.add_patch(this_rec)
            start_x += this_width

        # Label mass eigenstate
        this_ax.text(
            x,
            y,
            fr'$\mathrm{{m}}_{{{m_state}}}$ ',
            ha='right',
        )



    def add_flavour_legend(self):
        """
        Adds a legend showing which colour corresponds to which neutrino flavour.
        Assumes self.colours = [color_e, color_mu, color_tau].
        """
        # Names of the flavours
        flavour_names = [r'$\mathrm{e}$', r'$\mathrm{\mu}$', r'$\mathrm{\tau}$']

        # Create handles for the legend
        handles = [Patch(color=c, label=l) for c, l in zip(self.colours, flavour_names)]

        # Add the legend to the bottom panel
        self.fig.legend(handles=handles, loc='center right',
                        ncol=1, frameon=True, facecolor = 'white', framealpha = 1)





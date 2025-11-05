import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from .base import BasePlot

MASS_FILE = 'rrndbd/data/isobars136.csv'

class IsobarsPlot(BasePlot):
    '''A class for plotting the A = 136 isobars to demonstrate that Xe-136 must undergo double beta decay'''

    def __init__(self, **kwargs):
        '''Creates the isobar plot!'''

        super().__init__(**kwargs)

        ISOBARS = get_isobars().copy()

        # Even-Even
        ISOBARS.loc[(ISOBARS['z'] % 2 == 0) & (ISOBARS['n'] % 2 == 0), 'colour'] = self.colours[0]
        # Odd-Odd
        ISOBARS.loc[(ISOBARS['z'] % 2 == 1) & (ISOBARS['n'] % 2 == 1), 'colour'] = self.colours[1]

        for _, row in ISOBARS.iterrows():
            self.ax.text(
                row['z'], row['massExcess(MeV)'],
                r'$^{136}$' + row['name'][3:],
                ha='center', va='center',
                fontsize=10, weight='bold', color='white',
                bbox=dict(boxstyle='round,pad=0.5', fc=row['colour'], ec='black', lw=0.5)
            )

        self.ax.set_ylim(ISOBARS['massExcess(MeV)'].min() - 2, ISOBARS['massExcess(MeV)'].max() + 2)
        self.ax.set_xlim(ISOBARS['z'].min() - 1, ISOBARS['z'].max() + 2)

        self.ax.grid(which = 'both', axis = 'x')

        even_even_patch = mpatches.Patch(color=self.colours[0], label='Even–Even')
        odd_odd_patch  = mpatches.Patch(color=self.colours[1], label='Odd–Odd')

        self.ax.legend(
            handles=[even_even_patch, odd_odd_patch],
            loc='lower right',  # or 'best', 'upper left', etc.
            frameon=True,
            facecolor = 'white',
            title='Pairing',
            fontsize=9,
            title_fontsize=10,
            )

        # Basic plot formatting
        self.set_labels('Atomic Number, Z', 'Mass Excess [MeV]')

        self.fig.show()
    



def get_isobars(filename :str = MASS_FILE, isobar : int = 136, min_max = (53, 60)):
    '''This organizes the isobar data from the binding energy file (BE_FILE) and prepares it to be plotted. The global variable ISOBARS will point to it.'''

    global ISOBARS
    all = pd.read_csv(MASS_FILE)

    ISOBARS = all[all['z'] + all['n'] == isobar].copy()

    ISOBARS = ISOBARS[(ISOBARS['z'] >= min_max[0]) & (ISOBARS['z'] <= min_max[1])]
    ISOBARS['massExcess(MeV)'] = ISOBARS['massExcess(keV)']/1000

    # Add a label for plotting ease
    ISOBARS['label'] = ISOBARS.apply(lambda row: fr'$^{{{row['z'] + row['n']}}}${str(row['name'])[len(str(isobar)):]}', axis=1)

    ISOBARS = ISOBARS.sort_values('massExcessUncertainty').drop_duplicates(subset=['z', 'n'], keep='first')

    return ISOBARS
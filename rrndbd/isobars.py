import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from .constants import PROTON_MASS_MEV, NEUTRON_MASS_MEV, AMU_MEV
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

        # semf = ISOBARS.sort_values(by = 'z')

        # self.ax.plot(semf['z'], semi_empirical_mass_formula(semf['z'], semf['n']), label = 'SEMF')

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


def semi_empirical_mass_formula(z, n, mass_excess = False):
    '''Returns the value of the semi-empirical mass formula given various fitting parameters. If the "mass excess" option is selected, 
    The mass result absent the mass value based solely on protons and neutrons is returned.'''
    
    v = 15.85
    s = 18.34
    c = 0.71
    a = 92.86
    d = 11.46

    first = z*PROTON_MASS_MEV + n*NEUTRON_MASS_MEV
    vol = - v*(z + n)
    surf = s*(z + n)**(2/3)
    coul = c * z**2 / (n + z)**(1/3)
    # asy = a*(n - z)**2 / (n + z)
    delt = - (((-1)**z + (-1)**n)/2)*(d / np.sqrt(z + n))
    asy = a*(z - (n + z)/2)**2 / (z + n)

    mass = first + vol + surf + coul + asy + delt
    if mass_excess:
        return mass - AMU_MEV*(n + z)

    return mass


def main():

    this_plot = IsobarsPlot()
    this_plot.show()


if __name__ == '__main__':
    main()
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from .base import BasePlot

BE_FILE = 'rrndbd/data/binding_energy.csv'
ISOBARS = None

class IsobarsPlot(BasePlot):
    '''A class for plotting the A = 136 isobars to demonstrate that Xe-136 must undergo double beta decay'''
    

    def __init__(self, **kwargs):
        '''Creates the isobar plot!'''

        if ISOBARS is None:
            get_isobars()

        # Basic plot formatting
        self.set_labels('Atomic Number, Z', 'Binding Energy per Nucleon')
        self.ax.scatter(ISOBARS['z'], ISOBARS['bindingEnergy'])
    



def get_isobars(filename :str = BE_FILE, isobar : int = 136):
    '''This organizes the isobar data from the binding energy file (BE_FILE) and prepares it to be plotted. The global variable ISOBARS will point to it.'''

    global ISOBARS
    all = pd.read_csv(BE_FILE)

    ISOBARS = all[all['z'] + all['n'] == isobar].copy()

    # Add a label for plotting ease
    ISOBARS['label'] = ISOBARS.apply(lambda row: fr'$^{{{row['z'] + row['n']}}}${str(row['name'])[len(str(isobar)):]}', axis=1)
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from .base import BasePlot

XE_EXPS_CSV = 'rrndbd/data/xenon_experiments.csv'
XE_EXPS_DF = None


class XeExperimentPlot(BasePlot):
    '''A class for producing plots of xenon-based experiments over time. This plot motivates the search for new Xenon sources.'''

    def __init__(self, filename : str = XE_EXPS_CSV, names : bool = True):
        '''Creates the plot'''

        # Pulls the experiment data
        get_experiment_data(filename)
        exps = XE_EXPS_DF

        # Basic plot adjustments
        self.ax.set_yscale('log')
        self.set_labels('Reference Year', 'Xenon Mass [kg]')
        self.ax.set_ylim(1, 1e9); self.ax.set_xlim(2002, 2055)








def get_experiment_data(filename : str = XE_EXPS_CSV):
    '''This function reads the experiment data from a csv file and returns a pandas dataframe for making the plot'''

    global XE_EXPS_DF

    exps = pd.read_csv('data/xenon_experiments.csv')

    exps['enriched'] = False
    exps.loc[exps['xe136_percent'] > 8.9, 'enriched'] = True

    exps['nat_required'] = exps['xenon_kg']*exps['xe136_percent']/8.9
    exps['unf_required'] = exps['xenon_kg']*exps['xe136_percent']/43

    # Add a few more attributes for plotting ease
    exps['mark'] = None

    # Define a mapping of status -> marker
    marker_map = {
        'complete': '<',
        'ongoing': 'o',
        'planned': '>',
        'future': 'd'
    }

    # Apply the mapping to create a new 'mark' column
    exps['mark'] = exps['status'].map(marker_map)

    XE_EXPS_DF = exps





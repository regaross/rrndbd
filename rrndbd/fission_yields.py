from .base import BasePlot
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

FISSION_FILE = 'rrndbd/data/fission_yields.csv'

class FissionYieldPlot(BasePlot):
    '''A class for the nuclear fission product histograms. Can also show the Ashton binding energy curve '''

    def __init__(self, show_be : bool = True, **kwargs):
        '''A constructor for the fission yield plot. By default the plot shows the binding energy curve'''

        if show_be: 
            super().__init__(nrows = 2, **kwargs)
            self.be, self.fy = self.ax

        else:
            super().__init__(**kwargs)
            self.fy = self.ax


        data = get_fission_yields()
        fiss_center = int(data['a'].dot(data['fiss_sum'])/np.sum(data['fiss_sum']))
        mean_be = data['be_mean']; min_be = data['be_min']; max_be = data['be_max']
        left = (78,32)
        right = (123,35)

        self.fy.fill_betweenx((0, 0.5), left[0], np.sum(left), color = 'burlywood', alpha = 0.5)
        self.fy.fill_betweenx((0, 0.5), right[0], np.sum(right), color = 'burlywood', alpha = 0.5)
        width = 0.8
        self.fy.bar(data['a'], data['fiss_sum'], color = self.colours[1], width = width, align = 'center',)
        self.fy.set_xlim(fiss_center - 50, fiss_center + 50)
        self.fy.set_ylim(0,0.5)
        self.fy.set_ylabel(r'CFY of $^{235}$U')
        self.fy.set_xlabel(r'Nuclear Mass, A')

        if show_be:
            self.be.fill_between(data['a'], min_be, max_be, color = self.colours[0], label = 'All')
            self.be.plot(data['a'], mean_be, color = self.colours[1], label = "Mean")
            self.be.set_ylabel(r'BE / A  [MeV]')
            self.be.set_xlabel(r'Nuclear Mass, A')
            self.be.scatter(235, 7.55, color = self.colours[3], s = 60, zorder = 10)
            self.be.text(238, 7.65, r'$^{235}$U')
            left = (78,32)
            right = (123,35)
            prods1 = Rectangle((left[0], 7.6), left[1], 1.5, facecolor='burlywood', alpha=0.5, label = 'Fission Products')
            prods2 = Rectangle((right[0], 7.6), right[1],1.5, facecolor='burlywood', alpha=0.5)
            self.be.add_patch(prods1)
            self.be.add_patch(prods2)
            self.be.legend(loc = 'lower right')


        self.show()





def get_fission_yields(filename: str = FISSION_FILE):
    """Reads in the CSV file with the fission product data and computes 
    summed fission product yields and binding energy statistics grouped by A."""
    
    nuke_data = pd.read_csv(filename)
    nuke_data['a'] = nuke_data['z'] + nuke_data['n']
    nuke_data['MeV'] = nuke_data['bindingEnergy'] / 1000

    grouped = (
        nuke_data
        .groupby('a', as_index=False)
        .agg(
            fiss_sum=('cFY235U', 'sum'),
            be_mean=('MeV', 'mean'),
            be_min=('MeV', 'min'),
            be_max=('MeV', 'max')
        )
    )

    return grouped
from .base import BasePlot, TwoPanelBasePlot
import pandas as pd
import matplotlib.pyplot as plt


atmosgas = pd.read_csv('rrndbd/data/atmosgas.csv')
# drop the "air" record.
atmosgas = atmosgas[atmosgas['name'] != 'air']

xe_isotopes = pd.read_csv('rrndbd/data/xenon_isotopes.csv')

class GasBarPlot(BasePlot):

    def __init__(self, ax=None, **kwargs):
        super().__init__(ax=ax, **kwargs)
        
        self.ax.set_title('Atmospheric Gas Composition')
        self.ax.set_ylabel('Volume Fraction')
        self.ax.bar(atmosgas['label'], atmosgas['volume_fraction'])
        self.ax.set_yscale('log')


class XenonIsoPlot(BasePlot):

    def __init__(self, ax=None, **kwargs):
        super().__init__(ax=ax, **kwargs)

        xe_isotopes['label'] = [str(int(m)) for m in xe_isotopes['mass']]
        self.ax.set_title('Natural Xenon Isotopes')
        self.ax.bar(xe_isotopes['label'], xe_isotopes['nat_fraction'], color = self.colours[1])
        self.set_labels('Mass Number A', 'Fraction')
        


class AtmosXePlot(TwoPanelBasePlot):

    def __init__(self, **kwargs):
        super().__init__(gridspec_kw={'width_ratios': [3, 2]}, **kwargs)

        atm = GasBarPlot(self.ax1)
        xeiso = XenonIsoPlot(self.ax2)

        self.show()


        

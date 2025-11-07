import matplotlib.pyplot as plt
from .style import set_plot_style

class BasePlot:
    def __init__(self, figsize = (6,4), **kwargs):
        set_plot_style()
        self.fig, self.ax = plt.subplots(figsize = figsize, **kwargs)
        self.colours = plt.rcParams['axes.prop_cycle'].by_key()['color']

    def set_labels(self, xlabel = None, ylabel = None, title = None):
        if xlabel: self.ax.set_xlabel(xlabel)
        if ylabel: self.ax.set_ylabel(ylabel)
        if title: self.ax.set_title(title)

    def show(self):
        plt.show()
    
    def save(self, filename):
        self.fig.savefig(filename, bbox_inches = 'tight')

    def logscalexy(self):
        '''Sets both x and y axes on a log scale.'''
        self.ax.set_xscale('log')
        self.ax.set_yscale('log')
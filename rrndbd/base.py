import matplotlib.pyplot as plt
from .style import set_plot_style

class BasePlot:
    def __init__(self, ax=None, figsize=(6,4), **kwargs):
        set_plot_style()
        
        if ax is None:
            self.fig, self.ax = plt.subplots(figsize=figsize, **kwargs)
        else:
            self.ax = ax
            self.fig = ax.figure  # link to the figure containing this ax
            
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

    def set_xscale(self, value, **kwargs):
        self.ax.set_xscale(value, **kwargs)

    def set_yscale(self, value, **kwargs):
        self.ax.set_yscale(value, **kwargs)

class TwoPanelBasePlot():
    """
    Generic two-panel plot class.
    Provides self.ax1 and self.ax2 for plotting side by side.
    """
    def __init__(self, figsize=(10,5), **kwargs):
        set_plot_style()  # your custom style
        self.fig, (self.ax1, self.ax2) = plt.subplots(1, 2, figsize=figsize, **kwargs)
        self.colours = plt.rcParams['axes.prop_cycle'].by_key()['color']

    def set_titles(self, title1=None, title2=None):
        if title1:
            self.ax1.set_title(title1)
        if title2:
            self.ax2.set_title(title2)

    def set_suptitle(self, suptitle):
        self.fig.suptitle(suptitle, y=1.01)

    def set_labels(self, xlabel=None, ylabel=None, xlabel2=None, ylabel2=None):
        if xlabel:
            self.ax1.set_xlabel(xlabel)
        if ylabel:
            self.ax1.set_ylabel(ylabel)
        if xlabel2:
            self.ax2.set_xlabel(xlabel2)
        if ylabel2:
            self.ax2.set_ylabel(ylabel2)

    def show(self):
        plt.tight_layout()
        plt.show()

    def save(self, filename):
        self.fig.savefig(filename, bbox_inches='tight')

    def logscalexy(self, ax1=False, ax2=False):
        """Set log scale on either axis or both."""
        if ax1:
            self.ax1.set_xscale('log')
            self.ax1.set_yscale('log')
        if ax2:
            self.ax2.set_xscale('log')
            self.ax2.set_yscale('log')

from .base import BasePlot
from .constants import fetch_neutrino_constants
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve
import yaml


_NEUTRINO_CONSTANTS = fetch_neutrino_constants()
DSM21 = (_NEUTRINO_CONSTANTS['dsm21']['value'], _NEUTRINO_CONSTANTS['dsm21']['error'])
DSM32 = (_NEUTRINO_CONSTANTS['dsm32']['value'], _NEUTRINO_CONSTANTS['dsm32']['error'])
SST12 = (_NEUTRINO_CONSTANTS['sst12']['value'], _NEUTRINO_CONSTANTS['sst12']['error'])
SST13 = (_NEUTRINO_CONSTANTS['sst13']['value'], _NEUTRINO_CONSTANTS['sst13']['error'])
SST23 = (_NEUTRINO_CONSTANTS['sst23']['value'], _NEUTRINO_CONSTANTS['sst23']['error'])
DCP =   (_NEUTRINO_CONSTANTS['dcp']['value'],   _NEUTRINO_CONSTANTS['dcp']['error'])

# Empty dictionary to house the experimental constraints on this parameter space
CONSTRAINTS = {}
PATH_TO_CONSTRAINTS = 'rrndbd/data/nu_mass_constraints.yml'

class LobsterPlot(BasePlot):

    def __init__(self, min_masses = None, 
                cosmo_constraint : bool = True, 
                beta_constraint : bool = True,
                bdnd_constraint : bool = True, **kwargs):
        '''Initializes a bare neutrinoless double beta decay lobster plot with
        both mass orderings shown on two surfaces.'''
        # Initialize the parent object
        super().__init__(**kwargs)

        ## Plot x data:
        self.min_masses = min_masses if min_masses is not None else np.logspace(-4,0,100)

        ## Plot look and labels:
        self.xlabel = r'$m_{\mathrm{lightest}}$ [eV]'
        self.ylabel = r'$\langle m_{\beta\beta}\rangle$ [eV]'
        self.set_labels(self.xlabel, self.ylabel)
        self.logscalexy()
        self.edgecolor = plt.rcParams['axes.edgecolor']
        self.xlim = (1e-4, 1e0)
        self.ylim = (1e-4, 1e0)
        self.ax.set_ylim(self.ylim[0], self.ylim[1])
        self.ax.set_xlim(self.xlim[0], self.xlim[1])

        self.draw_hierarchies()
        self.add_mass_sum_constraint()
        self.add_beta_decay_constraint()



    def draw_hierarchies(self, min_masses=None, uncertainty = False):
        '''Populates the plot with the normal and inverted hierarchy surfaces allowed by the parameter space. '''

        if min_masses is not None:
            self.min_masses = min_masses

        # Inverted Hierarchy
        inv_min, inv_max = majorana_mass_bounds(self.min_masses, True)
        self.ax.plot(self.min_masses, inv_min, color = self.edgecolor, lw = 1)
        self.ax.plot(self.min_masses, inv_max, color = self.edgecolor, lw = 1)
        self.ax.fill_between(self.min_masses, inv_min, inv_max, alpha = 0.8)
        self.ax.text(1.6e-4, 2.6e-2, 'Inverted Ordering', fontdict = {'size' : 15})

        # Normal Hierarchy
        nor_min, nor_max = majorana_mass_bounds(self.min_masses, False)
        self.ax.plot(self.min_masses, nor_min, color = self.edgecolor, lw = 1)
        self.ax.plot(self.min_masses, nor_max, color = self.edgecolor, lw = 1)
        self.ax.fill_between(self.min_masses, nor_min, nor_max, alpha = 0.8)
        self.ax.text(1.6e-4, 2e-3, 'Normal Ordering', fontdict = {'size' : 15})

    def add_mass_sum_constraint(self, key: str  = ''):
        '''With a given upper limit on the sum of neutrino masses (as from cosmological fits) this function plots constraints in both lightest neutrino mass, and effective Majorana mass. If majorana, the constraint is shown on the effective Majorana mass, too.'''
        global CONSTRAINTS
        if not CONSTRAINTS: load_constraints_from_yaml(PATH_TO_CONSTRAINTS)

        # Possible future feature of changing the constraint in-code as opposed to in the yaml
        if not bool(key):
            key = CONSTRAINTS['defaults']['cosmology']

        mass_sum = CONSTRAINTS['cosmology'][key]['nu_mass_sum']
        label = CONSTRAINTS['cosmology'][key]['label']

        xmax, ymax = self.xlim[1], self.ylim[1]

        # Find the corresponding lightest neutrino masses
        mmin_nrm = mass_sum_to_lightest(mass_sum)
        mmin_inv = mass_sum_to_lightest(mass_sum, True)

        # Find the corresponding Majorana Masses
        meff_nrm = mass_sum_to_majorana(mass_sum)
        meff_inv = mass_sum_to_majorana(mass_sum, True)

        if mmin_inv < 0:
            # The inverted hierarchy suggests an "unphysical" mass, we say it's disfavoured.
            ymax = meff_nrm
            xmax = mmin_nrm

        self.plot_constraint(xmax, ymax, color = self.colours[3], label = label)

    def add_beta_decay_constraint(self, key : str = ''):
        '''With a given upper limit on the effective electron neutrino mass (as from KATRIN) this function plots constraints in both lightest neutrino mass, and effective Majorana mass. If majorana, the constraint is shown on the effective Majorana mass, too.'''
        global CONSTRAINTS
        if not CONSTRAINTS: load_constraints_from_yaml(PATH_TO_CONSTRAINTS)

        # Possible future feature of changing the constraint in-code as opposed to in the yaml
        if not bool(key):
            key = CONSTRAINTS['defaults']['beta_decay']

        nu_e_mass = CONSTRAINTS['beta_decay'][key]['nu_e_mass']
        label = CONSTRAINTS['beta_decay'][key]['label']

        mmin = nu_e_mass_to_lightest(nu_e_mass)
        meff = nu_e_mass_to_majorana(nu_e_mass)

        self.plot_constraint(mmin, meff, label = label, color = self.colours[5]) 

    def plot_constraint(self, mmin_max, meff_max, label = '', **kwargs):
        '''Taking the two maximum values meff and mmin, we plot a rectangular region on the bottom left of the plot.'''

        xmin, xmax = self.xlim[0]*0.9, self.xlim[1]*1.1
        ymin, ymax = self.ylim[0]*0.9, self.ylim[1]*1.1

        if meff_max < ymax:
            ymax = meff_max
        if mmin_max < xmax:
            xmax = mmin_max

        self.ax.plot([xmin, xmax, xmax], [ymax, ymax, ymin], linestyle = '--', **kwargs)
        self.ax.text(xmax*0.6, ymax*0.9, label, va = 'top', ha = 'right', **kwargs)

def load_constraints_from_yaml(filename):

    '''Given the filename of a yaml file, this loads it into the global CONSTRAINTS dictionary. This will be where plotting scripts look.'''
    global CONSTRAINTS
    with open(filename, 'r') as f:
        data = yaml.safe_load(f)
        if isinstance(data, dict):
            CONSTRAINTS.update(data)


def majorana_mass_bounds(min_masses, inverted = False):
    '''Computes the upper and lower bounds of the normal hierarchy
    parameter space based on the Majorana phase values.'''
    
    if not inverted:
        max = eff_majorana_mass(min_masses, 0, 0)
        min = np.piecewise(min_masses, \
            [min_masses < 0.0024, (min_masses >= 0.0024) \
            & (min_masses < 0.0064), min_masses >= 0.0064], \
            [lambda x: eff_majorana_mass(x, np.pi, 0), \
            0, lambda x: eff_majorana_mass(x, np.pi, np.pi)])
    else:
        min = eff_majorana_mass(min_masses, np.pi, np.pi, True)
        max = eff_majorana_mass(min_masses, 0, 0, True)
    
    return min, max


def neutrino_masses(mmin, inverted=False, increasing = False):
    '''Returns the neutrino masses based on a minimum mass,
    the squared mass differences, and the assumption that neutrino
    masses are positive values.'''

    if not inverted:    # Normal hierarchy m1 < m2 < m3
        m1 = mmin
        m2 = np.sqrt(mmin**2 + DSM21[0], dtype=complex)
        m3 = np.sqrt(m2**2 + abs(DSM32[0]), dtype=complex)
        return m1.real, m2.real, m3.real

    else:               # Inverted hierarchy m3 < m1 < m2
        m3 = mmin
        m2 = np.sqrt(m3**2 + abs(DSM32[0]), dtype=complex)
        m1 = np.sqrt(m2**2 - DSM21[0], dtype=complex)
    
        if not increasing:
            return m1.real, m2.real, m3.real
        else:
            return m3.real, m1.real, m2.real


def eff_majorana_mass(mmin, pa, pb, inverted = False) -> np.ndarray:
    '''A function that calculates the effective Majorana mass using 
    the pdg neutrino information, namely, mixing parameters and mass 
    differences. pa and pb are Majorana phases.'''

    m1, m2, m3 = neutrino_masses(mmin, inverted)

    term1 = (1 - SST12[0])*(1 - SST13[0])*m1
    term2 = SST12[0]*(1 - SST13[0])*m2*np.exp(1j*pa)
    term3 = SST13[0]*m3*np.exp(1j*pb)

    return abs(term1 + term2 + term3)

def electron_neutrino_mass(mmin, inverted = False):
    '''Given the lightest neutrino mass, this function returns the effective
    electron neutrino mass under either normal or inverted ordering.'''

    m1, m2, m3 = neutrino_masses(mmin, inverted)

    term1 = np.sqrt((1 - SST12[0])*(1 - SST13[0]))*m1
    term2 = np.sqrt(SST12[0]*(1 - SST13[0]))*m2
    term3 = np.sqrt(SST13[0])*m3*np.exp(1j*DCP[0])

    return abs(term1 + term2 + term3)


def nu_mass_sum(mmin, inverted = False):
    ''' Returns the sum of the neutrino masses within the specified hierarchy'''

    m1, m2, m3 = neutrino_masses(mmin, inverted)

    return m1 + m2 + m3

def mass_sum_to_lightest(summass, inverted = False):
    '''Given the sum of neutrino masses, this function returns what the maximum lightest neutrino mass must be under normal or inverted ordering'''

    sumdiff = lambda mmin : nu_mass_sum(mmin, inverted) - summass

    return fsolve(sumdiff, 0.05)[0]


def mass_sum_to_majorana(summass, inverted = False):
    '''Given the sum of the neutrino masses, this function returns what the maximum
    effective Majorana mass can be under normal or inverted ordering.'''

    mmin = mass_sum_to_lightest(summass, inverted)

    return eff_majorana_mass(mmin, 0, 0, inverted)


def nu_e_mass_to_lightest(nu_e_mass, inverted = False):
    '''With an effective electron neutrino mass, this function computes the lightest neutrino mass under normal or inverted ordering.'''

    massdiff = lambda mmin : electron_neutrino_mass(mmin, inverted) - nu_e_mass

    return fsolve(massdiff, 0.05)[0]

def nu_e_mass_to_majorana(nu_e_mass, inverted = False):
    '''With an effective electron neutrino mass, this function computes the maximum effective Majorana mass under normal or inverted ordering.'''
    
    mmin = nu_e_mass_to_lightest(nu_e_mass, inverted)

    return eff_majorana_mass(mmin, 0, 0, inverted)


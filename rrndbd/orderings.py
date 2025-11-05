import numpy as np
import matplotlib.pyplot as plt
from .base import BasePlot
from .constants import fetch_neutrino_constants, pmns
from .lobster import neutrino_masses

_NEUTRINO_CONSTANTS = fetch_neutrino_constants()
DSM21 = (_NEUTRINO_CONSTANTS['dsm21']['value'], _NEUTRINO_CONSTANTS['dsm21']['error'])
DSM32 = (_NEUTRINO_CONSTANTS['dsm32']['value'], _NEUTRINO_CONSTANTS['dsm32']['error'])
SST12 = (_NEUTRINO_CONSTANTS['sst12']['value'], _NEUTRINO_CONSTANTS['sst12']['error'])
SST13 = (_NEUTRINO_CONSTANTS['sst13']['value'], _NEUTRINO_CONSTANTS['sst13']['error'])
SST23 = (_NEUTRINO_CONSTANTS['sst23']['value'], _NEUTRINO_CONSTANTS['sst23']['error'])
DCP =   (_NEUTRINO_CONSTANTS['dcp']['value'],   _NEUTRINO_CONSTANTS['dcp']['error'])

class OrderingPlot(BasePlot):
    '''A plot of the neutrino mass orderings showing the decomposition of the mass eigenstates into their flavours'''
    
    # Flavour decomposition of mass eigenstates (for plotting colours)
    m1 = np.array([1,0,0])
    m1d = np.abs(pmns@m1)**2
    m2 = np.array([0,1,0])
    m2d = np.abs(pmns@m2)**2
    m3 = np.array([0,0,1])
    m3d = np.abs(pmns@m3)**2


import numpy as np
from scipy.special import loggamma  # used only in relativistic branch if needed
from scipy.constants import physical_constants, alpha
from .base import BasePlot
import matplotlib.pyplot as plt
from numpy import trapezoid, expm1

# electron rest energy in MeV (from scipy.constants)
m_e = physical_constants["electron mass energy equivalent in MeV"][0]  # MeV


class TritiumBetaPlot(BasePlot):

    def __init__(self):
        super().__init__()
        T, spectrum, gauss = tritium_beta_spectrum()
        self.ax.plot(T*1000, gauss*100 - 1, label = 'Expected')
        self.ax.plot(T[:450]*1000, spectrum[:450] - 1, label = 'Measured')
        self.set_labels('Electron energy keV', r'$dN/dE$ [Arb. Units]')
        self.ax.set_ylim(0, 105)

def tritium_beta_spectrum():
    m_e = 0.51099895  # MeV
    E0 = 0.0186      # Tritium endpoint in MeV

    T = np.linspace(0, E0*1.1, 500)   # kinetic energy (MeV)
    E = T + m_e
    p = np.sqrt(E**2 - m_e**2)


    # --- Add narrow Gaussian "two-body decay" peak at endpoint ---
    peak_center = E0
    peak_sigma = 0.00002   # 20 eV in MeV (adjust narrower/wider as needed)
    gauss_peak = np.exp(-(T - peak_center)**2 / (2 * peak_sigma**2))

    spectrum = p * E * (E0 - T)**2
    print(np.trapezoid(spectrum, T))
    spectrum /= np.trapezoid(spectrum, T)  # normalize for display

    # Scale peak so it's visible but small
    # gauss_peak *= spectrum.max() * 0.1

    return T, spectrum, gauss_peak
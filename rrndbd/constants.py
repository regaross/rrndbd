import pdg
import numpy as np
from scipy.constants import physical_constants

# Module-level cache
_NEUTRINO_CONSTANTS = None
ELECTRON_MASS_MEV = physical_constants['electron mass energy equivalent in MeV']
_PMNS = None

def fetch_neutrino_constants():
    '''Fetch neutrino mixing parameters from PDG API, cached after first call.'''
    global _NEUTRINO_CONSTANTS
    if _NEUTRINO_CONSTANTS is None:
        api = pdg.connect()

        # Define the PDG IDs we want
        mixing = {
            'sst12': {'pdgid': 'S067P12'},  # sine-squared of theta-12
            'sst13': {'pdgid': 'S067P13'},  # sine-squared of theta-13
            'sst23': {'pdgid': 'S067P23'},  # sine-squared of theta-23
            'dsm21': {'pdgid': 'S067DM3'},  # delta-m-squared of states 2-1
            'dsm32': {'pdgid': 'S067DM1'},  # delta-m-squared of states 3-2
            'dcp':   {'pdgid': 'S067DEL'},  # Dirac CP-violating phase
        }

        # Initialize the global dictionary
        _NEUTRINO_CONSTANTS = {}

        # Populate it with data from the API
        for param, info in mixing.items():
            pdg_obj = api.get(info['pdgid'])
            # Convert PdgProperty attributes to a dict
            _NEUTRINO_CONSTANTS[param] = {attr: getattr(pdg_obj, attr) for attr in vars(pdg.data.PdgProperty) if not attr.startswith("_")}

    return _NEUTRINO_CONSTANTS

def pmns():
    """Compute and cache the PMNS (Pontecorvo–Maki–Nakagawa–Sakata) mixing matrix.

    Returns
    -------
    numpy.ndarray
        3×3 complex PMNS matrix using PDG 2025 convention.
    """
    global _PMNS
    if _PMNS is not None:
        return _PMNS

    # Fetch mixing constants (sin²θ and δCP)
    const = fetch_neutrino_constants()

    # Convert sine² values to radians
    s12 = np.sqrt(const['sst12']['value'])
    s13 = np.sqrt(const['sst13']['value'])
    s23 = np.sqrt(const['sst23']['value'])
    c12, c13, c23 = np.sqrt(1 - s12**2), np.sqrt(1 - s13**2), np.sqrt(1 - s23**2)

    # Dirac CP phase in radians
    delta_cp_deg = const['dcp']['value']
    delta_cp = np.deg2rad(delta_cp_deg)

    # --- PDG 2025 convention ---
    # U = R23 * R13 * R12
    U = np.array([
        [c12 * c13, s12 * c13, s13 * np.exp(-1j * delta_cp)],
        [
            -s12 * c23 - c12 * s23 * s13 * np.exp(1j * delta_cp),
            c12 * c23 - s12 * s23 * s13 * np.exp(1j * delta_cp),
            s23 * c13,
        ],
        [
            s12 * s23 - c12 * c23 * s13 * np.exp(1j * delta_cp),
            -c12 * s23 - s12 * c23 * s13 * np.exp(1j * delta_cp),
            c23 * c13,
        ],
    ], dtype=complex)

    _PMNS = U
    return _PMNS
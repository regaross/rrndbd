import pdg
from scipy.constants import physical_constants

# Module-level cache
_NEUTRINO_CONSTANTS = None
ELECTRON_MASS_MEV = physical_constants['electron mass energy equivalent in MeV']

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

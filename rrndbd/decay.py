import numpy as np
import urllib.request
import pandas as pd
from periodictable import elements
from pyne.material import Material
from pyne import nucname, data




def decay(pyne_inventory, seconds):
    '''Given an inventory of isotopes, this will use Pyne to "decay" them for `seconds` seconds. 
    The isotope inventory should be in numbers of atoms, or fractions of atoms. Yeah atom is a weird word for this, but this is what Pyne does.'''

    # seconds = np.concatenate([[0], seconds])
    total_atoms = sum(pyne_inventory.values())

    initial = Material() 

    # Define the material in terms of fractional constituents.
    # Pyne takes care of the normalization.
    initial.from_atom_frac(pyne_inventory)

    return initial.decay(seconds)


def parse_pyne_id(nuc_id, element = True):
    """Extract Z and A from PyNE nuclide ID"""
    Z = nuc_id // 10000000
    A = (nuc_id % 10000000) // 10000

    if element:
        element = elements[Z]
        return f"{element.symbol}{int(A)}"
    
    else:
        return Z, A



def cum_decay_count(initial, check_seconds):
    '''This function is intended to determine the maximum number of each isotope present in the inventory (including the initial inventory)
    Accounting for the various decays that add and remove from specific isotope counts
    
    This isn't perfect. Fundamentally, this is to asnwer the question of what isotopes are created through decay processes following cosmogenic activation.'''

    # Retain the total for the sake of normalization
    total = sum(initial.values())

        # Set a "cumulative" dictionary to hold the initial values, and to update through the time iterations
    cumulative = {key: 
                  {'initial' : initial[key],
                   'max' : initial[key],
                   } for key in initial}
    

    # Define the material in terms of fractional constituents.
    # Pyne takes care of the normalization.
    inventory = Material() 
    inventory.from_atom_frac(initial)


    # For each timestep...
    for t in check_seconds:
        # Determine what the decay inventory would be after having decayed for t seconds
        decayed = inventory.decay(t).to_atom_frac()

        # For each isoTOPE in the decayed inventory
        for tope in decayed:
            amt = decayed[tope]

            # If it's already in our cumulative database...
            if tope in cumulative:
                if amt > cumulative[tope]['max']:
                     cumulative[tope]['max'] = amt
            # We need to add it.
            elif tope not in cumulative:
                cumulative[tope] = {'initial' : 0.0, 'max' : amt,}


    return cumulative




def make_pyne_id(Z, A):
    """Create PyNE nuclide ID from Z, A"""
    return Z * 10000000 + A * 10000 

def df_to_pyne_inventory(isotope_dataframe):

    isotope_dataframe['pyne'] = isotope_dataframe.apply(lambda row : make_pyne_id(row['Z'], row['A']), axis = 1 )

    return dict(zip(isotope_dataframe['pyne'], isotope_dataframe['count']))



def remove_hyphen(nuclide):
    '''Given a nuclide that looks like this: Xe-136, this silly little function turns it into this: Xe136.'''
    return nuclide.replace('-', '')


def seconds_to_readable(seconds):
    """Convert seconds to human-readable time"""
    if seconds == np.inf or seconds > 1e100:
        return "stable"
    elif seconds < 1e-6:
        return f"{seconds*1e9:.2f} ns"
    elif seconds < 1e-3:
        return f"{seconds*1e6:.2f} μs"
    elif seconds < 1:
        return f"{seconds*1e3:.2f} ms"
    elif seconds < 60:
        return f"{seconds:.2f} s"
    elif seconds < 3600:
        return f"{seconds/60:.2f} min"
    elif seconds < 86400:
        return f"{seconds/3600:.2f} hr"
    elif seconds < 3.156e7:
        return f"{seconds/86400:.2f} days"
    else:
        return f"{seconds/3.156e7:.2f} yr"
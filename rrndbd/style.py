import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path


STYLE_DIR = Path(__file__).parent / "mpl" / "styles"
AVAILABLE_THEMES = {
    "trading_card": STYLE_DIR / "trading_card.mplstyle",
}


TRADING_CARD_COLOURS = {
    'blue':     '#40798E',
    'butter':   '#F2DFC3',
    'green':    '#60722B',
    'deepred':  '#943225',
    'yellow':   '#EAB449',
    'black':    '#131813',
    'orange':   '#CB5433',
    'purple':   '#7F58AC',
    'brown':    '#82583A',
}

def set_plot_style(theme : str = 'trading_card'):
    '''Given a specific theme (mplstyle file), this function just turns it on.'''
    
    # Apply the chosen style
    plt.style.use(str(AVAILABLE_THEMES[theme]))

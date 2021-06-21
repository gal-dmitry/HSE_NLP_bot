from random import choice
from teenage_style import d_teenage
from stalker_style import d_stalker
from servant_style import d_servant


def style_init():
    global d_teenage
    global d_stalker
    global d_servant
    
    d_styles = [d_teenage, d_stalker, d_servant]
    d_style = choice(d_styles)
    
    return d_style
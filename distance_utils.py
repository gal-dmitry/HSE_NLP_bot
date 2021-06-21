from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps, formatting

from geopy.geocoders import Nominatim
from datetime import datetime, timedelta, timezone

from utils_for_bot import get_lemmas

from geopy.distance import great_circle

class Distance_Utils:

    def __init__(self):
        pass

    ### place ###
    def get_coords(self, city):
        coords = None
        address = None

        geolocator = Nominatim(user_agent='myapplication')
        location = geolocator.geocode(city)

        if location:
            lat, lon = location.latitude, location.longitude
            coords = (lat, lon)

        return coords
    
    def calc_distance(self, coords1, coords2):
        return great_circle(coords1, coords2).miles
        

    def get_city_from_rules(self, doc):
        locations = []
        for token in doc.tokens:
            if (token.pos in {'NOUN','PROPN'}) and (token.feats['Case'] == 'Loc'):
                locations.append(token.lemma)
        return locations


    def get_city_from_ner(self, doc):
        locations = []
        for span in doc.spans:
            loc = span.tokens[0].lemma
            for token in span.tokens[1:]:
                loc += f' {token.lemma}'
            locations.append(loc)
        return locations


    def get_cities(self, doc):
        ### костыли
        cities = []
        for token in doc.tokens:
            if token.text.lower() == 'спб':
                cities.append('Санкт-Петербург')

            if token.text.lower() == 'мск':
                cities.append('Москва')

        # если наташа определила локацию в тексте - вытащить ее
        if doc.spans:
            result = self.get_city_from_ner(doc)
            result.extend(cities)
            
            return result
        
        result = self.get_city_from_rules(doc)
        result.extend(cities)
    
        # найти в тексте: NOUN | PROPN, case=Loc
        return result


from utils_for_bot import to_lemmas
from weather_utils import Weather_Utils, WeatherForecaster
from anecdote_utils import JokeGenerator
from distance_utils import Distance_Utils
from random import choice


### MAIN CLASS ###

class Talker:
    def __init__(self, domain, words):
        self.domain = domain
        self.lemmas = to_lemmas(words) ## СПЕЦИФИЧНО ДЛЯ ТЕКУЩЕЙ РЕАЛИЗАЦИИ
        self.reset()

    def reset(self):
        self.entities = {}
        self.status = 'not'

    def process(self, parsed_message):
        pass

    def form_answer(self):
        pass



### CHAT CLASSES ###

# приветствие
class Greeting(Talker):
    def __init__(self, domain, words, phrases):
        super().__init__(domain, words)
        self.phrases = phrases
    
    def choose_phrase(self):
        return choice(self.phrases)

    def process(self, parsed_message):
        self.status = 'completed'

    def form_answer(self):
        self.status = 'not'
        answer = self.choose_phrase()
        
        return answer

# прощание
class Bye(Talker):
    def __init__(self, domain, words, phrases):
        super().__init__(domain, words)
        self.phrases = phrases
    
    def choose_phrase(self):
        return choice(self.phrases)

    def process(self, parsed_message):
        self.status = 'completed'
        
    def form_answer(self):
        self.status = 'not'
        answer = self.choose_phrase()
        
        return answer


# рассказать о своих функциях
class Presentation(Talker):
    def __init__(self, domain, words, phrases):
        super().__init__(domain, words)
        self.phrases = phrases
    
    def choose_phrase(self):
        return choice(self.phrases)
    
    def process(self, parsed_message):
        self.status = 'completed'
        
    def form_answer(self):
        self.status = 'not'
        answer = self.choose_phrase()
        
        return answer


# прекратить работу
class Alert(Talker):
    def __init__(self, domain, words):
        super().__init__(domain, words)
    
    def process(self, parsed_message):
        self.status = 'completed'
        
    def form_answer(self):
        self.status = 'not'
        return 'А это строка кстати не выведется'


# неизвестные темы
class Unknown(Talker):
    def __init__(self, domain, words, phrases):
        super().__init__(domain, words)
        self.phrases = phrases
    
    def choose_phrase(self):
        return choice(self.phrases)
    
    def process(self, parsed_message):
        self.status = 'completed'
        
    def form_answer(self):
        self.status = 'not'
        answer = self.choose_phrase()
        
        return answer


### SPECIAL CLASSES ###

# погода 
class Weather(Talker):

    def __init__(self, domain, words, OWM_API_KEY):
        super().__init__(domain, words)
        self.initialize_API(OWM_API_KEY)

    def reset(self):
        self.entities = {}
        self.entities['coords'] = None
        self.entities['address'] = None
        self.entities['time_count'] = None
        self.entities['time_unit'] = None
        self.status = 'not'

    def initialize_API(self, OWM_API_KEY):
        self.WEATHER_API = WeatherForecaster(OWM_API_KEY)
        self.WEATHER_CLASS = Weather_Utils()


    def process(self, parsed_message):

        # get entities
        if self.status == 'not':

            # адрес, координаты
            if self.entities['coords'] is None:
                address, coords = self.WEATHER_CLASS.get_location(parsed_message)
                if coords is not None:
                    self.entities['coords'] = coords
                    self.entities['address'] = address

            # кол-во: 1,2... , единица: неделя, день, час
            if self.entities['time_count'] is None:
                num, unit = self.WEATHER_CLASS.get_time(parsed_message)
                if unit is not None:
                    self.entities['time_count'] = num
                    self.entities['time_unit'] = unit
            
            # change status
            if self.entities['coords'] is not None \
            and self.entities['time_count'] is not None:
                self.status = 'completed'
       

    def form_answer(self):

        answer = ''

        if self.status == 'completed':
            address = self.entities['address']
            coords = self.entities['coords']

            unit = self.entities['time_unit']
            num = self.entities['time_count']

            forecast = self.WEATHER_API(unit, coords, num)
            answer = f"{address}\n\n{forecast}"

        else:
            answer_1 = None
            if self.entities['coords'] is None:
                answer_1 = 'место'

            if self.entities['time_count'] is None:
                if answer_1:
                    answer_1 += ' и дату'
                else:
                    answer_1 = 'дату'

            answer = f"Уточни пожалуйста {answer_1}!"

        return answer


class Anecdote(Talker):
    def __init__(self, domain, words):
        super().__init__(domain, words)
        self.joke_generator = JokeGenerator()

    def process(self, parsed_message):
        self.status = 'completed'
    
    def form_answer(self):
        self.status = 'not'
        joke = self.joke_generator.generate_joke()
        
        return joke


class Distance(Talker):

    def __init__(self, domain, words):
        super().__init__(domain, words)
        self.DISTANCE_CLASS = Distance_Utils()
        self.reset()

    def reset(self):
        self.entities = {}
        self.entities['first_city'] = None
        self.entities['second_city'] = None
        self.status = 'not'

    def process(self, parsed_message):

        # get entities
        if self.status == 'not':

            # адрес, координаты
            if not self.entities['first_city']:
                cities = self.DISTANCE_CLASS.get_cities(parsed_message)
                if len(cities) > 1:
                    self.entities['first_city'] = cities[0]
                    self.entities['second_city'] = cities[1]
            
            # change status
            if self.entities['first_city'] and self.entities['second_city']:
                self.status = 'completed'
       

    def form_answer(self):

        answer = ''

        if self.status == 'completed':            
            city1 = self.entities['first_city']
            city2 = self.entities['second_city']
            
            coords1 = self.DISTANCE_CLASS.get_coords(city1)
            coords2 = self.DISTANCE_CLASS.get_coords(city2)

            dist = self.DISTANCE_CLASS.calc_distance(coords1, coords2)
            answer = f"Расстояние между {city1} и {city2}: {dist} км"
            self.status = 'not'
        else:
            answer = f"Уточни пожалуйста оба города!"

        return answer

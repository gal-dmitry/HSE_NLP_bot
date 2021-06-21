from pyowm import OWM
from pyowm.utils import config
from pyowm.utils import timestamps, formatting

from geopy.geocoders import Nominatim
# from datetime import datetime, timedelta, timezone
from datetime import date as DATE

from utils_for_bot import get_lemmas, get_dates


COUNTS = {
'один':1,
'два':2,
'три':3,
'четыре':4,
'пять':5,
'шесть':6,
'семь':7,
'восемь':8,
'девять':9,
'десять':10,
'одиннадцать':11,
'двенадцать':12,
'тринадцать':13,
'четырнадцать':14,
'пятнадцать':15,
'шестнадцать':16,
'семнадцать':17,
'восемнадцать':18,
'девятнадцать':19,
'двадцать':20,
'тридцать':30,
'сорок':40,
'пятдесят':50,
'шестьдесят':60,
'семьдесят':70,
'восемьдесят':80,
'девяносто':90,
'сто':100,
}

COUNTS_int = set([str(i) for i in range(101)])

UNITS = {
'час':('hours', 'nothing'),
'сейчас':('hours', 0),
###
'день':('day', 'nothing'),
'сегодня':('day', 0),
'завтра':('day', 1),
'послезавтра':('day', 2),
###
'неделя':('week', 0)
}



### parse location and time from user message ###
class Weather_Utils:

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
            address = location.address

        return address, coords
        

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


    def get_city(self, doc):
        ### костыли
        for token in doc.tokens:
            if token.text.lower() in ['спб', 'петербург', 'питер', 'питере'] :
                return ['Санкт-Петербург']

            if token.text.lower() == 'мск':
                return ['Москва']

        # если наташа определила локацию в тексте - вытащить ее
        if doc.spans:
            return self.get_city_from_ner(doc)
    
        # найти в тексте: NOUN | PROPN, case=Loc
        return self.get_city_from_rules(doc)


    def get_location(self, doc):
        city = self.get_city(doc)
        address, coords = self.get_coords(city)
        return address, coords


    ### time ###
    def diff_dates(self, date1, date2):
        return abs(date2-date1).days


    def from_date(self, dates):
        date = dates[0].fact
        day, month, year = date.day, date.month, date.year
        curr_day, curr_month, curr_year = DATE.today().strftime("%d.%m.%Y").split('.')

        if not year:
            year = curr_year

        if not month:
            month = curr_month

        if not day:
            day = curr_day
        
        # print('day, month, year:', (day, month, year))
        # print('c_day, c_month, c_year:', (curr_day, curr_month, curr_year))

        d1 = DATE(int(curr_year), int(curr_month), int(curr_day))
        d2 = DATE(int(year), int(month), int(day))
        
        time_unit = 'day'
        time_count =  self.diff_dates(d1, d2)
        # print(time_count)
        return time_count, time_unit


    def from_text(self, key_lst, lemmas):

        time_unit, time_count = UNITS[key_lst[0]]
        if time_count == 'nothing': ### !!!

            # 1, 2, 3 ...
            ints = list(lemmas.intersection(COUNTS_int))
            if ints:
                time_count = int(ints[0])

            # words
            else:
                strs = list(lemmas.intersection(set(COUNTS.keys())))
                if strs:
                    time_count = sum([COUNTS[num] for num in strs])

            # count = 1
            if time_count == 'nothing': ### !!!
                time_count = 1
        
        return time_count, time_unit


    def get_time(self, doc):
        
        lemmas = get_lemmas(doc)
        time_count = None
        time_unit = None
        
        # check date
        dates = get_dates(doc)
        # print('dates:', dates)
        if dates:
            time_count, time_unit = self.from_date(dates)

        # hour, day, week
        else:
            key_lst = list(lemmas.intersection(set(UNITS.keys())))
            if key_lst:
                time_count, time_unit = self.from_text(key_lst, lemmas)

        return time_count, time_unit



### get forecast from API ###
class ParseForecast:

    def __init__(self, key):
        owm = OWM(key)
        self.mgr = owm.weather_manager()


    def __call__(self, mode, coords, time=1):
        lat, lon = coords
        one_call = self.mgr.one_call(lat=lat, lon=lon)
        
        # "return a forecast for a week"
        if mode == 'week':
            dct = one_call.forecast_daily
            week = []
            for i in range(7):
                week.append(self.get_info(dct[i], flag='week'))
            return week
        
        # "return a forecast for the day {x}"
        elif mode == 'day':
            dct = one_call.forecast_daily
            day = self.get_info(dct[time], flag='day')
            return day
        
        # "return a forecast for the next {x} hours"
        elif mode == 'hours':
            dct = one_call.forecast_hourly
            hours = []
            for i in range(time):
                hours.append(self.get_info(dct[i], flag='hour'))
            return hours
                
        else:
            raise ValueError()    
    
    
    def get_info(self, dct, flag=None):

        date, time = f"{formatting.timeformat(dct.ref_time, 'date')}".split()

        date = date.split('-')
        date[0], date[-1] = date[-1], date[0]
        date = '/'.join(date)

        time = time[:8]

        wind_speed = dct.wnd['speed']
        wind_degree = dct.wnd['deg']
        wind_gust = dct.wnd['gust']
        
        humidity = dct.humidity
        pressure = dct.pressure['press']
        
        status = dct.detailed_status
        perc_prob = dct.precipitation_probability
        #         rain = 
        #         snow = 
        
        if dct.temperature('celsius').get('temp', None):
            temp = round(dct.temperature('celsius').get('temp', None))
            temp_feel = round(dct.temperature('celsius').get('feels_like', None))
            visibility_distance = dct.visibility_distance
            
            
        else:
            min_temp = round(dct.temperature('celsius').get('min', None))
            max_temp = round(dct.temperature('celsius').get('max', None))
                    
            day_temp = round(dct.temperature('celsius').get('day', None))
            night_temp = round(dct.temperature('celsius').get('night', None))
            eve_temp = round(dct.temperature('celsius').get('eve', None))
            morn_temp = round(dct.temperature('celsius').get('morn', None))
            temp = [day_temp, night_temp, eve_temp, morn_temp]
            # temp = [day_temp, night_temp]
            
            day_temp_feel = round(dct.temperature('celsius').get('feels_like_day', None))            
            night_temp_feel = round(dct.temperature('celsius').get('feels_like_night', None))
            eve_temp_feel = round(dct.temperature('celsius').get('feels_like_eve', None))
            morn_temp_feel = round(dct.temperature('celsius').get('feels_like_morn', None))
            
            
        forecast = {'Дата:':date}
            
        if flag == 'week':
            
            forecast['Температура днем (*С):'] = day_temp
            forecast['Температура ночью (*С):'] = night_temp
            
            
        elif flag == 'hour':
            
            forecast['Время (UTC+0):'] = time
            forecast['Температура (*С):'] = temp
            forecast['Ощущается как (*С):'] = temp_feel
            forecast['Видимость (м):'] = visibility_distance
                
            
        elif flag == 'day':
            
            forecast['Максимальная температура (*С):'] = max_temp
            forecast['Минимальная температура (*С):'] = min_temp

            forecast['Днем: температура (*С):'] = day_temp
            forecast['Днем: ощущается как (*С):'] = day_temp_feel

            forecast['Ночью: температура (*С):'] = night_temp
            forecast['Ночью: ощущается как (*С):'] = night_temp_feel

            # forecast['Morning: температура (*С):'] = morn_temp
            # forecast['Morning: ощущается как (*С):'] = morn_temp_feel

            # forecast['Eve: температура (*С):'] = eve_temp
            # forecast['Eve: ощущается как (*С):'] = eve_temp_feel
            
            
        forecast['Статус:'] = status
        forecast['Вероятность осадков (%):'] = round(perc_prob * 100)
        if flag == 'week':
            return forecast
        
        forecast['Скорость ветра (м/c):'] = wind_speed
        forecast['Направление (deg):'] = wind_degree
        # forecast['Gust (???):'] = wind_gust
        
        forecast['Влажность (%):'] = round(humidity)
        forecast['Давление (мм рт.ст.):'] = pressure

        return forecast



class WeatherForecaster:

    def __init__(self, key):
        self.forecaster = ParseForecast(key)


    def __call__(self, mode, coords, time):
        if mode == 'week':
            return self.get_weather_for_a_week(coords)
        elif mode == 'day':
            return self.get_weather_for_a_day(coords, time)
        elif mode == 'hours':
            return self.get_weather_for_next_x_hours(coords, time)
        else:
            raise ValueError


    def get_weather_for_a_week(self, coords):
        """
        format:
        location
        {x7}
        ---
        date: year/month/day
        temperature_day: *C
        temperature_day: *C
        status: 
        precipitation_prob: %
        ---
        """
        week = self.forecaster('week', coords)
        forecast = ''
        for day in week:
            for key, value in day.items():
                forecast += key
                forecast += f' {value}'
                forecast += '\n'
            forecast += '\n'
        return forecast

    
    def get_weather_for_a_day(self, coords, day):
        """
        format:
        ---
        location
        date: day/month/year
        detailed forecast
        ---
        """
        if day > 7:
            return "Только на 7 дней вперед"
        
        day = self.forecaster('day', coords, time=day)
        forecast = ''
        for key, value in day.items():
            forecast += key 
            forecast += f' {value}'
            forecast += '\n'
        forecast += '\n'
        return forecast

    
    def get_weather_for_next_x_hours(self, coords, hours):
        """
        format:
        ---
        location
        {X}
        date: year/month/day
        Xst hour: detailed forecast
        ---
        """
        if hours > 12:
            return "Только на 12 часов вперед"
        
        hours = self.forecaster('hours', coords, time=hours)
        forecast = ''
        for hour in hours:
            for key, value in hour.items():
                forecast += key 
                forecast += f' {value}'
                forecast += '\n'
            forecast += '\n'
        return forecast
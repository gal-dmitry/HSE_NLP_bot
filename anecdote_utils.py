from bs4 import BeautifulSoup
import requests
from random import randint

class JokeGenerator:
    
    def __init__(self):
        self.cache = []
        self.urls = ['https://nekdo.ru/random/',
                     'http://anekdotme.ru/random']
        self.find_args = [('div', 'text'),
                          ('div', 'anekdot_text')]
    
    def add_url(self, url, args):
        self.urls.append(url)
        self.find_args.append(args)
    
    def upd_cache(self):
        ind = randint(0, len(self.urls) - 1)
        url = self.urls[ind]
        args = self.find_args[ind]

        page = requests.get(url).text
        soup = BeautifulSoup(page, 'html.parser')
        
        for t in soup.find_all(args[0], args[1]):
            self.cache.append(t.text.strip().replace('\n', ' '))
    
    def generate_joke(self):
        if not self.cache:
            self.upd_cache()
            
        joke = self.cache[0]
        del self.cache[0]

        return joke
    
    def clear_cache(self):
        self.cache = []

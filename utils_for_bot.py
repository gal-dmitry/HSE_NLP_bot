import telebot
from collections import defaultdict
from copy import deepcopy

from natasha import (
    Segmenter,
    MorphVocab,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,
    
    PER,
    NamesExtractor,
    DatesExtractor,

    Doc)


segmenter = Segmenter()
morph_vocab = MorphVocab()

emb = NewsEmbedding()
syntax_parser = NewsSyntaxParser(emb)
morph_tagger = NewsMorphTagger(emb)
ner_tagger = NewsNERTagger(emb)

names_extractor = NamesExtractor(morph_vocab)
dates_extractor = DatesExtractor(morph_vocab)


def case_punct(text):
    if not text[0].isupper():
        text = text[0].upper() + text[1:]
    if '.' not in text:
        text += '.'
    return text



def parse(text, mode='case_punct'):
    ### привести строку к "стандартному виду"
    if mode == 'case_punct':
        text = case_punct(text)

    ### прогнать через Natasha
    my_doc = Doc(text)
    my_doc.segment(segmenter)
    my_doc.tag_morph(morph_tagger)
    my_doc.parse_syntax(syntax_parser)
    my_doc.tag_ner(ner_tagger)

    # лемматизация
    for token in my_doc.tokens:
        token.lemmatize(morph_vocab)

    return my_doc



def get_lemmas(doc):
    return set([token.lemma for token in doc.tokens])


def get_dates(doc):
    return list(dates_extractor(doc.text))


def to_lemmas(words):
    set_lemmas = set()
    # взять леммы от ключевых слов
    for word in words:
        parsed_word = parse(word, mode=None)
        new_lemmas = get_lemmas(parsed_word)
        set_lemmas = set_lemmas.union(new_lemmas)
    return set_lemmas



class Domains:
    def __init__(self):
        self.domain_dict = defaultdict(set)
        
    def add_domain(self, domen_name, set_lemmas):

        # В ОБЩЕМ СЛУЧАЕ ЭТО НАВЕРНОЕ ДОЛЖЕН БЫТЬ
        # СЛОВАРЬ ПО ТИПУ {domain : function}
        # ГДЕ function ПОЗВОЛЯЕТ ОПРЕДЕЛИТЬ ИНТЕНЦИЮ

        self.domain_dict[domen_name].update(set_lemmas)


class Parser:
    def __init__(self, domain_dict):
        self.domains = domain_dict


    def __call__(self, text):
        parsed = self.parse_message(text)
        intentions = self.get_intention(parsed)
        return parsed, intentions


    def parse_message(self, text):
        return parse(text)


    def get_intention(self, parsed_message):
    
        set_lemmas = get_lemmas(parsed_message)
        # print(f"set_lemmas = {set_lemmas}")

        intentions = []

        # Распознавание интенций происходит путем сравнения лемм сообщения 
        # и лемм ключевых слов
        for key, value in self.domains.items():
            if set_lemmas.intersection(value):
                intentions.append(key)

        if not intentions:
            intentions.append('unknown')

        # print('intentions:', intentions)
        # print('intentions_type:', type(intentions))
        return intentions



class Buffer:
    def __init__(self):
        self.reset()

    def reset(self):
        self.is_empty = True
        self.talkers = []

    def add(self, talker):
        self.is_empty = False
        self.talkers.append(talker)



class Bot:

    def __init__(self, KEY):
        self.domains = Domains()
        self.parser = Parser(self.domains.domain_dict)
        self.buff = Buffer()
        self.talkers = {}

        self.bot = telebot.TeleBot(KEY)

        self.send_welcome = self.bot.message_handler(commands=['start', 'help'])(self.send_welcome)
        self.react_on_message = self.bot.message_handler(content_types=['text'])(self.react_on_message)


    def add_talker(self, talker):
        self.domains.add_domain(talker.domain, talker.lemmas)
        self.talkers[talker.domain] = talker


    def send_welcome(self, message):
        self.bot.reply_to(message, f'Я бот. Приятно познакомиться, {message.from_user.first_name}')


    def react_on_message(self, message):
        # парсинг сообщения и извлечение интенций
        parsed_message, intentions = self.parser(message.text)
        # print('buffer:', self.buff.talkers)
        # print(intentions)

        # проверка на "экстренное прерывание"
        if ('alert' in intentions) or ('bye' in intentions):
            # стереть всю историю сообщений
            self.buff.reset()
            # замолчать
            # print('пройдено')
            self.bot.send_message(message.from_user.id, 'молчу')
            return

        # если нет истории сообщений с пользователем
        if self.buff.is_empty:

            for intention in intentions:
                talker = deepcopy(self.talkers[intention])
                # ключевая функция - вычленение entities / определение статуса
                talker.process(parsed_message)
                # добавить в буфер talker
                self.buff.add(talker)

        # если пользователь что-то спрашивал, но нам не хватило информации
        else:
            # извлечение сущностей из нового сообщения для интенции из буфера
            talker = self.buff.talkers[0]
            talker.process(parsed_message)

        ### готовые сообщения
        completed_answers = []
        new_list = []
        for talker in self.buff.talkers:
            if talker.status == 'completed':
                answer = talker.form_answer()  # формирование ответа
                completed_answers.append(answer)
            else:
                new_list.append(talker)
    
        self.buff.reset()
        if new_list:
            self.buff.talkers = new_list
            self.buff.is_empty = False

        for answer in completed_answers:
            self.bot.send_message(message.from_user.id, answer)


        ### спросить недостающую информацию
        if not self.buff.is_empty:
            talker = self.buff.talkers[0]
            answer = talker.form_answer()
            self.bot.send_message(message.from_user.id, answer)
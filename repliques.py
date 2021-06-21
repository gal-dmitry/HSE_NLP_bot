from collections import defaultdict as ddict


REPLIQUES = ddict(list)

REPLIQUES['bye'] = ['пока', 'прощай', 'удачи', 'бай']
REPLIQUES['unknown'] = ['unknown']
REPLIQUES['greetings'] = ['привет', 'здравствуй', 'хелло']
REPLIQUES['presentation'] = ['представь', 'умеешь', 'функции']

REPLIQUES['alert'] = ['конец']
REPLIQUES['distance'] = ['расстояние']
REPLIQUES['anecdote'] = ['анекдот', "шутка", "смешнявка", "история",
                         "посмеяться", "смеяться", "рассмеяться",
                         "поржать", "поугарать", "смешить",
                         "насмешить", "рассмешить", "угарать"]

REPLIQUES['weather'] = ['погода', 'климат', 'температура', 'ветер']


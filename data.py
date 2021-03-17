import copy
import json
from pdb import set_trace as T

import yaml

with open('novel/novel_old.json') as f:
    old_game = json.load(f)

scenes = old_game['scenes']
old_scene = scenes[0]

with open('data/countries.yaml') as f:
    countries = yaml.load(f)
# with open('data/countries.json') as f:
#    countries = json.load(f)

new_game = copy.deepcopy(old_game)

countries = countries['countries']

choices = []

for code, c_name in countries.items():
    choices.append({
        'name': code,
        'text': 'Go to {}'.format(c_name),
        'nextScene': code,
    })

new_scenes = []

for code, c_name in countries.items():
    travel_choices = copy.deepcopy(choices)
    travel_choices.append({
        'name': 'trade_{}'.format(code),
        'text': 'Trade with {}'.format(c_name),
        'nextScene': 'trade_{}'.format(code),
    })
    country_scene = copy.deepcopy(old_scene)
    country_scene.update({
        'name': code,
        'text': c_name,
        'choices': travel_choices,
    })
    new_scenes.append(country_scene)

    trade_choices = [{
        'name': 'travel',
        'text': 'Return to travel',
        'nextScene': code,
        }]
    trade_scene = copy.deepcopy(old_scene)
    trade_scene.update({
        'name': 'trade_{}'.format(code),
        'text': "Trading with {}".format(c_name),
        'choices': trade_choices
    })
    new_scenes.append(trade_scene)

new_game['scenes'] = new_scenes

with open('novel/novel.json', 'w') as f:
    json.dump(new_game, f, indent=4)

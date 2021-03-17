import copy
import pandas
import numpy as np
import json
from pdb import set_trace as T

import yaml

with open('novel/novel_old.json') as f:
    old_game = json.load(f)

scenes = old_game['scenes']
old_scene = scenes[0]

with open('data/countries.yaml') as f:
    countries = yaml.load(f, yaml.Loader)
# with open('data/countries.json') as f:
#    countries = json.load(f)

df = pandas.read_csv('data/trading.csv')
items = np.array(list(df['Item']))

new_game = copy.deepcopy(old_game)

new_inventories = [[] for i in range(6)]

items_inventory = []
np.random.shuffle(items)
items = items[:20]

for i in items:

    i_dict = {
        'name': i,
        'value': 1,
        'hidden': False,
            }
    items_inventory.append(i_dict)

old_inventories = old_game['inventories']
new_inventories[1] = old_inventories[1] + items_inventory
new_inventories[0] = old_inventories[0] + items_inventory
assert len(new_inventories) == len(old_game['inventories'])
new_game['inventories'] = new_inventories

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
    travel_choices = []
    travel_choices.append(copy.deepcopy(choices))
    travel_choices.append({
        'name': 'trade_{}'.format(code),
        'text': 'Trade with {}'.format(c_name),
        'nextScene': 'trade_{}'.format(code),
    })
    country_scene=copy.deepcopy(old_scene)
    country_scene.update({
        'name': code,
        'text': c_name,
        'choices': travel_choices,
    })
    new_scenes.append(country_scene)

    trade_choices=[{
        'name': 'travel',
        'text': 'Return to travel',
        'nextScene': code,
        }]
    country_df = df[df['Area'] == c_name]
    trade_scene=copy.deepcopy(old_scene)
    trade_scene.update({
        'name': 'trade_{}'.format(code),
        'text': "Trading with {}".format(c_name),
        'choices': trade_choices
    })
    new_scenes.append(trade_scene)

new_game['scenes']=new_scenes

with open('novel/novel.json', 'w') as f:
    json.dump(new_game, f, indent=4)

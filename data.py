import copy
import json
from pdb import set_trace as T

import numpy as np
import pandas
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
        'value': 0,
        'hidden': False,
    }
    items_inventory.append(i_dict)

old_inventories = old_game['inventories']
new_inventories[0] = items_inventory
#new_inventories[1] = old_inventories[1] + items_inventory
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

new_game['settings']['scrollSettings'] = {'defaultScrollSpeed': 0}

for code, c_name in countries.items():
    travel_choices = copy.deepcopy(choices)
    travel_choices= [{
        'name': 'trade_{}'.format(code),
        'text': 'Trade with {}'.format(c_name),
        'nextScene': 'trade_{}'.format(code),
    }] + travel_choices
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
    country_df = df[df['Area'] == c_name]
    exports = country_df[country_df['Element'] ==
            'Export Quantity'].sort_values('Value')[-10:]
    for x in exports.iloc:
        item = x['Item']
        quantity = x['Value']
        unit = x['Unit']
        flag = x['Flag Description']
        trade_choices.append(
            {
                'name': item,
                'text': 'Buy 1 of {} {} of {}'.format(
                    quantity, unit, item),
                #TODO: track country inventories!
    #           'nextScene': 'trade_{}'.format(code),
                'nextScene': code,
                'addItem': "{},1".format(item)
                })
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

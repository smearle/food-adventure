import copy
from scipy.sparse.csgraph import minimum_spanning_tree
import json
from pdb import set_trace as T

import numpy as np
import pandas
import yaml

with open('novel/novel_old.json') as f:
    old_game = json.load(f)

scenes = old_game['scenes']
old_scene = scenes[0]

#with open('data/countries.yaml') as f:
#    countries = yaml.load(f, yaml.Loader)
with open('data/countries.json') as f:
   countries = json.load(f)

#dists_df = pandas.read_csv('data/country_distances.csv', header=None)
dists_df = pandas.read_csv('country-distance/output/distance-matrix.csv', header=0)
borders_df = pandas.read_csv('data/borders.csv')
borders_df = borders_df.where(pandas.notnull(borders_df), None)

adj_arr = dists_df.to_numpy()[:,1:].astype(np.float)
adj_arr = minimum_spanning_tree(adj_arr).toarray()
span_df = dists_df.copy()
span_df.iloc[:, 1:] = adj_arr

iso_codes = span_df.iloc[:, 0]
iso_codes = iso_codes.where(pandas.notnull(iso_codes), None)
iso_codes = list(span_df.iloc[:, 0])

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


countries = {c['code']: c['name'] for c in countries}
#countries = countries['countries']
#countries['TL'] = 'East Timor'
#countries['SS'] = 'South Sudan'

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
    travel_choices = []
    neighbors = \
        borders_df[borders_df['country_code'] == code]['country_border_code']
    neighbors = neighbors.where(pandas.notnull(neighbors), None)
    neighbors = list(neighbors)
    # if no land neighbors, provide some water routes

    if code not in iso_codes:
        print('Warning: no distances found for {}'.format(c_name))
    else:
        span_nbs = span_df[span_df['Unnamed: 0'] == code].to_numpy()[0,1:]
        idxs = span_nbs.nonzero()[0]
        for i in idxs:
            nb_code = iso_codes[i]
            neighbors.append(nb_code)
    for n in neighbors:
        if n is None:
            continue
        if n not in countries:
            print('Error with {}'.format(n))
            continue
        travel_choices.append({
            'name': n,
            'text': 'Go to {}'.format(countries[n]),
            'nextScene': n,
        })


   #if len(neighbors) ==1 and neighbors[0] is None or len(neighbors) == 0:
   #    neighbors = dists_df[dists_df[0] == code]
    if len(neighbors) == 0:
        print('Warning: no neighbors found for {}'.format(c_name))
    #   travel_choices = copy.deepcopy(choices)
    travel_choices = [{
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
        trade_choices.append({
            'name':
            item,
            'text':
            'Buy 1 of {} {} of {}'.format(quantity, unit, item),
            # TODO: track country inventories!
            #           'nextScene': 'trade_{}'.format(code),
            'nextScene':
            code,
            'addItem':
            "{},1".format(item)
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

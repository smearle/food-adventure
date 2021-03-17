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

def parse_name_str(str):
    return str.replace(' ','_').replace(',','_').replace('(','_')

dists_dict_df = pandas.read_csv('data/country_distances.csv', header=None)
dists_df = pandas.read_csv('data/distance-matrix.csv', header=0)
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
# In case we want to limit number of items in the game
#items = items[:]

items_inventory.append(
    {'name': 'money',
     'value': 100000000,
     'hidden': False,}
)

for i in items:

    i = parse_name_str(i)
    i_dict = {
        'name': i,
        'value': 0,
        'hidden': False,
    }
    items_inventory.append(i_dict)

old_inventories = old_game['inventories']
new_inventories[0] = items_inventory
new_inventories[1] = [
    {'name': 'money',
     'value': 1000000,
     'hidden': False, }
]
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

country_nbs = {code: set() for code in countries.keys()}

for code, c_name in countries.items():
    neighbors = \
        borders_df[borders_df['country_code'] == code]['country_border_code']
    neighbors = neighbors.where(pandas.notnull(neighbors), None)
    neighbors = set(neighbors)
    # if no land neighbors, provide some water routes

    dist_neighbors = dists_df[dists_df['Unnamed: 0'] == code]
    if dist_neighbors.shape[0] == 0:
        dist_neighbors = dists_df[dists_df['Unnamed: 0'] == np.random.choice(iso_codes)]
    dist_arr = dist_neighbors.to_numpy()[0, 1:]
    dist_arr = sorted(list((dist, iso_codes[i]) for (i, dist) in enumerate(dist_arr)), key=lambda t: t[0])
    dist_neighbors = [t[1] for t in dist_arr[:10]]
    [neighbors.add(d) for d in dist_neighbors]

    if code not in iso_codes:
        print('Warning: no distances found for {}'.format(c_name))
    else:
        span_nbs = span_df[span_df['Unnamed: 0'] == code].to_numpy()[0, 1:]
        idxs = span_nbs.nonzero()[0]
        for i in idxs:
            nb_code = iso_codes[i]
            neighbors.add(nb_code)

        span_nbs_2 = span_df[code].to_numpy()
        idxs = span_nbs.nonzero()[0]
        for i in idxs:
            nb_code = iso_codes[i]
            neighbors.add(nb_code)
    country_nbs[code] = neighbors
    for nb_code in neighbors:
        if nb_code in country_nbs:
            country_nbs[nb_code].add(code)

for code, c_name in countries.items():

    added_nbs = set()
    travel_choices = []
    neighbors = country_nbs[code]
    for n in neighbors:
        if n is None or n in added_nbs:
            continue
        if n not in countries:
            print('Error with {}'.format(n))
            continue
        travel_choices.append({
            'name': n,
            'text': 'Go to {}'.format(countries[n]),
            'nextScene': n,
        })
        added_nbs.add(n)


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
        item_name = parse_name_str(item)
        quantity = x['Value']
        unit = x['Unit']
        flag = x['Flag Description']
        ex_val = country_df[country_df['Item'] == item][country_df['Element'] == 'Export Value']
        ex_price = ex_val['Value'].iloc[0]
        price_unit = ex_val['Unit'].iloc[0]
        trade_choices.append({
            'name':
            item,
            'text':
            'Buy 1 {} for {} x {} (of {} {} exported)'.format(item, ex_price, price_unit, quantity, unit),
            # TODO: track country inventories!
            'nextScene': 'trade_{}'.format(code),
#           'nextScene':
#           code,
            'addItem':
            "{},1*(inv.money>0)".format(item_name),
            'removeItem':
                "money,{}".format(ex_price)
        })

    imports = country_df[country_df['Element'] == 'Import Quantity'].sort_values('Value')[-10:]


    for i in imports.iloc:
        item = i['Item']
        item_name = parse_name_str(item)
        quantity = i['Value']
        unit = i['Unit']
        flag = i['Flag Description']
        im_val = country_df[country_df['Item'] == item][country_df['Element'] == 'Import Value']
        im_price = im_val['Value'].iloc[0]
        price_unit = im_val['Unit'].iloc[0]
        trade_choices.append({
            'name':
                'sell_{}'.format(item),
            'text':
                'Sell 1 {} for {} x {}, (of {} {} imported)'.format(item, im_price, price_unit, quantity, unit),
            # TODO: track country inventories!
            #           'nextScene': 'trade_{}'.format(code),
            'nextScene': 'trade_{}'.format(code),
            'removeItem':
                "{},1".format(item_name),
            'addItem':
                "money,{}*inv.{},1".format(im_price, item_name)
        })

    trade_scene = copy.deepcopy(old_scene)
    trade_scene.update({
        'name': 'trade_{}'.format(code),
        'text': "Trading with {}".format(c_name),
        'choices': trade_choices
    })
    new_scenes.append(trade_scene)

np.random.shuffle(new_scenes)
new_game['scenes'] = new_scenes

with open('novel/novel.json', 'w') as f:

    json.dump(new_game, f, indent=4)

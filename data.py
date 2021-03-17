import copy
from pdb import set_trace as T
import json

with open('novel/novel_old.json') as f:
    old_game = json.load(f)

scenes = old_game['scenes']
old_scene = scenes[0]

import yaml

with open('data/countries.yaml') as f:
    countries = yaml.load(f)
#with open('data/countries.json') as f:
#    countries = json.load(f)

new_game = copy.deepcopy(old_game)

new_scenes = []

countries = countries['countries']

choices = []
for code, c_name in countries.items():
    choices.append(
            {
                'name': code,
                'text': 'Go to {}'.format(c_name),
                'nextScene': code,
            })

for code, c_name in countries.items():
    scene = copy.deepcopy(old_scene)
    scene['name'] = code
    scene['text'] = c_name
    scene['choices'] = choices
    new_scenes.append(scene)

new_game['scenes'] = new_scenes

with open('novel/novel.json', 'w') as f:
    json.dump(new_game, f, indent=4)

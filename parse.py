#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function

import imp
from lex import tokens
from os import listdir, makedirs, path
from ply.yacc import yacc
from pprint import pprint
import argparse
import codecs
import json
import operator
import re
import ruamel.yaml as yaml
import sys
import ntpath
from game_objects import Army, ArmyAttachment, BuildablePop, Building, \
    Component, Edict, Policy, Resource, SpaceportModule, Technology, \
    TechnologyJSONEncoder, TileBlocker
from os.path import expanduser

config = imp.load_source('config', 'config.py')


# Process CLI arguments:
def valid_label(label):
    if not re.match(r'^\w+$', label):
        raise argparse.ArgumentTypeError('Must match [a-z0-9_]')
    elif label not in config.mods.keys():
        raise argparse.ArgumentTypeError('Unsupported mod')
    elif not path.isdir(path.join('public', label)):
        makedirs(path.join('public', label))

    return label.lower()


def valid_dirs(directory):
    if not path.isdir(directory):
        message = "'{}' not found or not a directory".format(directory)
        raise argparse.ArgumentTypeError(message)

    return directory

arg_parser = argparse.ArgumentParser(
    description='Parse Stellaris tech and localization files')
arg_parser.add_argument('mod', type=valid_label, help="Mod used (vanilla possible).")

args = arg_parser.parse_args()

mod_descs=[]
mod_descs.append(config.mods[args.mod])
i=0
while 1:
  if i>=len(mod_descs):
    break
  if type(mod_descs[i]) is list:
    for modName in reversed(mod_descs[i]):
      # print(modName)
      try:
        mod_descs.insert(i+1,config.mods[modName])
      except KeyError:
        print("ERROR:Unsupported mod in config file: {}".format(modName))
        raise
    del mod_descs[i]
  else:
    i+=1
mod_descs=reversed(mod_descs) #mods have to be in inverse loading order (vanilla is first and will be overwritten!)

tree_label = args.mod
directories = [config.game_dir]

for mod_desc in mod_descs:
  if type(mod_desc) is int:
    mod_dir = path.join(config.workshop_dir, str(mod_desc), 'mod')
  elif type(mod_desc) is str:
    mod_dir = expanduser(mod_desc)
  else:
    print("Invalid mod config! Must either be mod id or path. Given: {!s}".format(mod_desc))
    continue
  directories.append(mod_dir)


def p_script(tokens):
    'script : statements'
    tokens[0] = tokens[1]


def p_statement_statements(tokens):
    'statements : statement statements'
    tokens[0] = tokens[1] + tokens[2]


def p_statements_empty(tokens):
    'statements : empty'
    tokens[0] = []


def p_empty(tokens):
    'empty :'
    pass


def p_key(tokens):
    '''key : STRING
           | BAREWORD'''
    tokens[0] = tokens[1]


def p_keys(tokens):
    'keys : key keys'
    tokens[0] = [tokens[1]] + tokens[2] if type(tokens[1]) is str else \
                [tokens[1], tokens[2]]


def p_keys_empty(tokens):
    'keys : empty'
    tokens[0] = []


def p_statement_var_assign(tokens):
    'statement : VARIABLE EQUALS NUMBER'
    number = int(tokens[3]) if '.' not in tokens[3] else float(tokens[3])
    tokens[0] = [{tokens[1]: number}]


def p_statement_binop(tokens):
    'statement : binop'
    tokens[0] = tokens[1]


def p_expression_variable(tokens):
    'expression : VARIABLE'
    tokens[0] = tokens[1]


def p_expression_key(tokens):
    'expression : key'
    tokens[0] = tokens[1]

def p_expression_number(tokens):
    'expression : NUMBER'
    tokens[0] = tokens[1]


def p_binop(tokens):
    '''binop : key EQUALS expression
             | key GTHAN expression
             | key GEQUALS expression
             | key LEQUALS expression
             | key LTHAN expression'''
    operator = tokens[2]

    if re.match(r'^-?\d+$', str(tokens[3])):
        roperand = int(tokens[3])
    elif re.match(r'^-?\d+\.\d+$', str(tokens[3])):
        roperand = float(tokens[3])
    else:
        roperand = tokens[3]


    tokens[0] = [{tokens[1]: roperand}] if operator == '=' else \
                [{tokens[1]: {operator: roperand}}]


def p_list(tokens):
    '''list : LBRACE keys RBRACE'''
    tokens[0] = tokens[2]


def p_expression_list(tokens):
    'expression : list'
    tokens[0] = tokens[1]


def p_block(tokens):
    'block : LBRACE statements RBRACE'
    tokens[0] = tokens[2]


def p_expression_block(tokens):
    'expression : block'
    tokens[0] = tokens[1]


def p_error(p):
    raise Exception("Syntax error in input: {}".format(str(p)))


def get_file_paths(file_paths, directory):
    if not path.isdir(directory):
        # print("does not exist"+directory)
        return file_paths

    for filename in listdir(directory):
        file_path = path.join(directory, filename)
        if not path.isfile(file_path) \
           or 'README' in file_path \
           or not file_path.endswith('.txt'):
            continue

        print('loading {} ...'.format(filename))

        # If filename already loaded, replace old one with new:
        path_to_delete = next(iter(
            file_path for file_path
            in file_paths
            if path.basename(file_path) == filename
        ), None)
        if path_to_delete is not None:
            print('replacing {} ...'.format(path.basename(path_to_delete)))
            file_paths.remove(path_to_delete)

        file_paths.append(path.join(directory, filename))

    return file_paths


def localized_strings():
    loc_data = { }
    for file_path in loc_file_paths:
        filename = path.basename(file_path)
        print('loading {} ...'.format(filename))

        # Coerce Paradox's bastardized YAML into compliance
        not_yaml_lines = codecs.open(file_path, 'r', 'utf-8-sig').readlines()
        not_yaml = ''
        for line in not_yaml_lines:
            quote_instances = [i for i, char in enumerate(line)
                               if char == u'"']

            if len(quote_instances) >= 2:
                # Some lines have invalid data after terminal quote:
                last = quote_instances[-1]
                line = line[:last + 1] + '\n'

                if len(quote_instances) > 2:
                    second = quote_instances[1]
                    line = line[0:second] \
                           + line[second:last].replace(u'"', ur'\"') \
                           + line[last:]

            not_yaml += line

        still_not_yaml = re.sub(ur'£\w+  |§[A-Z!]', '', not_yaml)
        resembles_yaml = re.sub(r'(?<=\w):\d ?(?=")', ': ', still_not_yaml)
        resembles_yaml = re.sub(r'(?<=\w):\d\d ?(?=")', ': ', resembles_yaml)
        actual_yaml = re.sub(r'^[ \t]+', '  ', resembles_yaml, flags=re.M)

        file_data = yaml.load(actual_yaml, Loader=yaml.Loader)
        loc_map = file_data['l_english']
        try:
            loc_data.update(loc_map)
        except TypeError:
            print('Unable to find head YAML key for {}'.format(filename))
            sys.exit()

    for data in loc_data:
        if len(loc_data[data]) and loc_data[data][0] == '$':
            try:
                for ref in re.findall(r"\$(.*?)\$", loc_data[data], re.DOTALL):
                    loc_data[data] = loc_data[data].replace('${}$'.format(ref), loc_data[ref])
                    if ref == 'REACTOR_BOOSTER_1_DESC':
                        print('$'+ref+'$')
                        print(loc_data[ref])
                        print(loc_data[data])
            except KeyError:
                print('Warning: {} could not be localized'.decode('utf-8').format(ref))


    return loc_data

tech_file_paths = []
army_file_paths = []
army_attachment_file_paths = []
building_file_paths = []
buildable_pop_file_paths = []
component_file_paths = []
edict_file_paths = []
policy_file_paths = []
resource_file_paths = []
spaceport_module_file_paths = []
tile_blocker_file_paths = []
loc_file_paths = []
skip_terms = ['^events?', 'tutorials?', 'pop_factions?', 'name_lists?',
              'messages?', 'mandates?', 'projects?', 'sections?',
              'triggers?', 'traits?']
has_skip_term = re.compile(r'(?:{})_'.format('|'.join(skip_terms)))

for directory in directories:
    tech_dir = path.join(directory, 'common/technology')
    tech_file_paths = get_file_paths(tech_file_paths, tech_dir)

    army_dir = path.join(directory, 'common/armies')
    army_file_paths = get_file_paths(army_file_paths, army_dir)

    army_attachment_dir = path.join(directory, 'common/army_attachments')
    army_attachment_file_paths = get_file_paths(army_attachment_file_paths,
                                                army_attachment_dir)

    buildable_pop_dir = path.join(directory, 'common/buildable_pops')
    buildable_pop_file_paths = get_file_paths(buildable_pop_file_paths,
                                              buildable_pop_dir)

    building_dir = path.join(directory, 'common/buildings')
    building_file_paths = get_file_paths(building_file_paths, building_dir)

    component_dir = path.join(directory, 'common/component_templates')
    component_file_paths = get_file_paths(component_file_paths, component_dir)

    edict_dir = path.join(directory, 'common/edicts')
    edict_file_paths = get_file_paths(edict_file_paths, edict_dir)

    policy_dir = path.join(directory, 'common/policies')
    policy_file_paths = get_file_paths(policy_file_paths, policy_dir)

    resource_dir = path.join(directory, 'common/strategic_resources')
    resource_file_paths = get_file_paths(resource_file_paths, resource_dir)

    spaceport_module_dir = path.join(directory, 'common/spaceport_modules')
    spaceport_module_file_paths = get_file_paths(spaceport_module_file_paths,
                                                 spaceport_module_dir)

    tile_blocker_dir = path.join(directory, 'common/tile_blockers')
    tile_blocker_file_paths = get_file_paths(tile_blocker_file_paths,
                                                 tile_blocker_dir)

    loc_dir = path.join(directory, 'localisation/english')
    loc_file_paths += [path.join(loc_dir, filename) for filename
                       in listdir(loc_dir)
                       if path.isfile(path.join(loc_dir, filename))
                       and filename.endswith('l_english.yml')
                       and not has_skip_term.search(filename)]

loc_data = localized_strings()

pdx_tech_scripts = '\r\n'.join([open(file_path).read() for file_path
                                in tech_file_paths])
pdx_army_scripts = '\r\n'.join([open(file_path).read() for file_path
                                in army_file_paths])
pdx_army_attachment_scripts = '\r\n'.join([open(file_path).read() for file_path
                                           in army_attachment_file_paths])
pdx_buildable_pop_scripts = '\r\n'.join([open(file_path).read() for file_path
                                         in buildable_pop_file_paths])
pdx_building_scripts = '\r\n'.join([open(file_path).read() for file_path
                                    in building_file_paths])
pdx_component_scripts = '\r\n'.join([open(file_path).read() for file_path
                                     in component_file_paths])
pdx_edict_scripts = '\r\n'.join([open(file_path).read() for file_path
                                 in edict_file_paths])
pdx_policy_scripts = '\r\n'.join([open(file_path).read() for file_path
                                  in policy_file_paths])
pdx_resource_scripts = '\r\n'.join([open(file_path).read() for file_path
                                    in resource_file_paths])
pdx_spaceport_module_scripts = '\r\n'.join([open(file_path).read()
                                            for file_path
                                            in spaceport_module_file_paths])
pdx_tile_blocker_scripts = '\r\n'.join([open(file_path).read()
                                        for file_path
                                        in tile_blocker_file_paths])
yacc_parser = yacc()

def parse_scripts(file_paths):
    parsed = []

    for file_path in file_paths:
        print('parsing {} ...'.format(path.basename(file_path)))
        contents = open(file_path).read()
        # New Horizons mod has their own YAML corruption
        if args.mod == 'new_horizon' and "jem'hadar" in contents:
            print('fixing New Horizons YAML ...')
            contents = contents.replace("_jem'hadar", "_jem_hadar")

        parsed += yacc_parser.parse(contents)

    return parsed
tech_file_paths=sorted(tech_file_paths,key=ntpath.basename,reverse=True)
# print(tech_file_paths)
parsed_scripts = {'technology': parse_scripts(tech_file_paths),
                  'army': parse_scripts(army_file_paths),
                  'army_attachment': parse_scripts(army_attachment_file_paths),
                  'buildable_pop': parse_scripts(buildable_pop_file_paths),
                  'building': parse_scripts(building_file_paths),
                  'component': parse_scripts(component_file_paths),
                  'edict': parse_scripts(edict_file_paths),
                  'policy': parse_scripts(policy_file_paths),
                  'resource': parse_scripts(resource_file_paths),
                  'spaceport_module': parse_scripts(spaceport_module_file_paths),
                  'tile_blocker': parse_scripts(tile_blocker_file_paths)}

armies = [Army(entry, loc_data)
          for entry in parsed_scripts['army']
          if not entry.keys()[0].startswith('@')]
army_attachments = [ArmyAttachment(entry, loc_data)
                    for entry in parsed_scripts['army_attachment']
                    if not entry.keys()[0].startswith('@')]
buildable_pops = [BuildablePop(entry, loc_data)
                  for entry
                  in parsed_scripts['buildable_pop']
                  if not entry.keys()[0].startswith('@')]
buildings = [Building(entry, loc_data)
             for entry
             in parsed_scripts['building']
             if not entry.keys()[0].startswith('@')]
components = [Component(entry.values()[0], loc_data)
              for entry
              in parsed_scripts['component']
              if not entry.keys()[0].startswith('@')]
edicts = [Edict(entry.values()[0], loc_data)
          for entry
          in parsed_scripts['edict']
          if not entry.keys()[0].startswith('@')]
policies = [Policy(entry, loc_data)
            for entry
            in parsed_scripts['policy']
            if not entry.keys()[0].startswith('@')]
resources = [Resource(entry, loc_data)
             for entry
             in parsed_scripts['resource']
             if not entry.keys()[0].startswith('@')]
spaceport_modules = [SpaceportModule(entry, loc_data)
                     for entry
                     in parsed_scripts['spaceport_module']
                     if not entry.keys()[0].startswith('@')]
tile_blockers = [TileBlocker(entry, loc_data)
                 for entry
                 in parsed_scripts['tile_blocker']
                 if not entry.keys()[0].startswith('@')]
at_vars = {}
technologies = []

for entry in parsed_scripts['technology']:
    if entry.keys()[0].startswith('@'):
        at_var = entry.keys()[0]
        at_vars[at_var] = entry[at_var]
        continue

    if args.mod == 'primitive':
        start_with_tier_zero = False
    else:
        start_with_tier_zero = True
    redundant=False
    for existing_tech in technologies:
      if existing_tech.key==entry.keys()[0]:
        print("Removed reduntant tech {}".format(existing_tech.key))
        redundant=True
        continue
    if redundant:
      continue

    tech = Technology(entry, armies, army_attachments, buildable_pops,
                      buildings, components, edicts, policies, resources,
                      spaceport_modules, tile_blockers, loc_data, at_vars,
                      start_with_tier_zero)

    #if not tech.is_start_tech \
      # and tech.base_weight * tech.base_factor == 0 \
      # and len(tech.weight_modifiers) == 0:
        #print(tech.key)
        #continue

    technologies.append(tech)

keyList=[]
for tech in technologies:
  keyList.append(tech.key)
  # print(tech.weight_modifiers)

for tech in technologies:
  i=0
  while 1:
    # print(tech.prerequisites)
    if i>=len(tech.prerequisites):
      break;

    # print(tech.prerequisites[i])
    if tech.prerequisites[i] in keyList:
      i+=1
    else:
      print("Removed missing prerequisite tech {}".format(tech.prerequisites[i]))
      del tech.prerequisites[i]
  if len(tech.prerequisites)>1:
    for i,techRequ in enumerate(tech.prerequisites):
      if i==0:
        continue
      # tech.prerequisite_names.append(technologies[keyList.index(techRequ.key)].name)
      tech.prerequisite_names.append(u'\u2022 {}\n'.format(technologies[keyList.index(techRequ)].name.strip('"')))

technologies.sort(key=operator.attrgetter('tier'))
technologies.sort(
    key=lambda tech: {'physics': 1, 'society': 2, 'engineering': 3}[tech.area])
jsonified = json.dumps(technologies, indent=2, separators=(',', ': '),
                       cls=TechnologyJSONEncoder)

open(path.join('public', tree_label, 'techs.json'), 'w').write(jsonified)

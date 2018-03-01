# -*- coding: utf-8 -*-

from pprint import pprint
import re
import ruamel.yaml as yaml
import sys

localization_map = {}

def parse(modifier, loc_data):
    global localization_map
    localization_map = loc_data

    if len(modifier) == 1:
        modifier.append({'always': 'yes'})

    try:
        factor = next(iter(key for key in modifier
                           if key.keys()[0] == 'factor'))['factor']
        adjustment = _localize_factor(factor)
    except StopIteration:
        add = next(iter(line for line in modifier
                        if line.keys()[0] == 'add'))['add']
        adjustment = _localize_add(add)

    unparsed_conditions = [line for line in modifier \
                           if line.keys()[0] not in ['factor', 'add']]
    if len(unparsed_conditions) > 1:
        unparsed_conditions = [{'AND': unparsed_conditions}]

    conditions = [_parse_condition(condition)
                  for condition
                  in unparsed_conditions]

    yaml_output = yaml.dump({adjustment: conditions}, indent=4,
                            default_flow_style=False,
                            allow_unicode=True).decode('utf-8')
    pseudo_yaml = re.sub(ur'(\xd7[\d.]+):\n\s*- ', r'(\1)',
                         yaml_output).replace('- ', u'• ')
    return pseudo_yaml


def _parse_condition(condition):
    key = condition.keys()[0]
    value = condition[key]
    try:
        return globals()['_localize_' + key.lower()](value)
    except KeyError:
        print("Warning: "+'_localize_' + key.lower()+" missing")
        return key.lower()


def _localize_factor(factor):
    return u'\xD7{}'.format(factor)


def _localize_add(add):
    sign = '' if add == 0 else '+' if add > 0 else '-';
    return '{}{}'.format(sign, add)


def _localize_has_ethic(value):
    ethic = localization_map[value]
    return 'Has {} Ethic'.format(ethic)


def _localize_has_not_ethic(value):
    ethic = localization_map[value]
    return 'Does NOT have {} Ethic'.format(ethic)


def _localize_has_civic(value):
    civic = localization_map[value]
    return 'Has {} Government Civic'.format(civic)


def _localize_has_valid_civic(value):
    civic = localization_map[value]
    return 'Has {} Government Civic'.format(civic)


def _localize_has_not_civic(value):
    civic = localization_map[value]
    return 'Does NOT have {} Government Civic'.format(civic)


def _localize_has_ascension_perk(value):
    perk = localization_map[value]
    return 'Has {} Ascension Perk'.format(perk)


def _localize_has_megastructure(value):
    megastructure = localization_map[value]
    return 'Has Megatructure {}'.format(megastructure)


def _localize_has_policy_flag(value):
    policy_flag = localization_map[value]
    return 'Has {} Policy'.format(policy_flag)


def _localize_has_trait(value):
    trait = localization_map[value]
    return 'Has {} Trait'.format(trait)

def _localize_has_authority(value):
    authority = localization_map[value]
    return 'Has {} Authority'.format(authority)

def _localize_has_not_authority(value):
    authority = localization_map[value]
    return 'Does NOT have {} Authority'.format(authority)

def _localize_host_has_dlc(dlc):
    # dlc = localization_map[value]
    return 'Host does has the {} DLC'.format(dlc)

def _localize_host_has_not_dlc(dlc):
    # dlc = localization_map[value]
    return 'Host does NOT have the {} DLC'.format(dlc)

def _localize_has_technology(value):
    try:
        technology = localization_map[value]
    except KeyError:
        technology = value

    return 'Has {} Technology'.format(technology)


def _localize_has_not_technology(value):
    try:
        technology = localization_map[value]
    except KeyError:
        technology = value

    return 'Does NOT have {} Technology'.format(technology)


def _localize_has_modifier(value):
    modifier = localization_map[value]
    return 'Has the {} modifier'.format(modifier)


def _localize_has_not_modifier(value):
    modifier = localization_map[value]
    return 'Does NOT have the {} modifier'.format(modifier)


def _localize_is_country_type(value):
    return 'Is of the {} country type'.format(value)


def _localize_ideal_planet_class(value):
    return 'Is ideal class'.format(value)


def _localize_is_planet_class(value):
    planet_class = localization_map[value]
    return 'Is {}'.format(planet_class)


def _localize_has_government(value):
    government = localization_map[value]
    return 'Has {}'.format(government)


def _localize_has_not_government(value):
    government = localization_map[value]
    return 'Does NOT have {}'.format(government)


def _localize_is_colony(value):
    return 'Is a Colony' if value == 'yes' \
        else 'Is NOT a Colony'


def _localize_is_ftl_restricted(value):
    return 'FTL is restricted' if value == 'yes' \
        else 'FTL is NOT restricted'

def _localize_has_any_megastructure_in_empire(value):
    return 'Has any Megastructure' if value == 'yes' \
        else 'Has NO Megastructures'


def _localize_allows_slavery(value):
    return 'Allows Slavery' if value == 'yes' \
        else 'Does NOT allow Slavery'


def _localize_has_federation(value):
    return 'Is in a Federation' if value == 'yes' \
        else 'Is NOT in a Federation'

def _localize_num_owned_planets(value):
    operator, value = _operator_and_value(value)
    return 'Number of owned planets is {} {}'.format(operator, value)

def _localize_count_owned_pops(value):
    operator, value = _operator_and_value(value[1]['count'])
    return 'Number of enslaved planets {} {}'.format(operator, value)

def _localize_num_communications(value):
    operator, value = _operator_and_value(value)
    return 'Number of owned planets is {} {}'.format(operator, value)


def _localize_has_communications(value):
    return 'Has communications with your Empire'


def _localize_is_ai(value):
    return 'Is AI controlled' if value == 'yes' else 'Is NOT AI controlled'


def _localize_is_same_species(value):
    localized_value = 'Dominant' \
                      if value.lower() == 'root' \
                         else localization_map[value]
    return 'Is of the {} Species'.format(localized_value)


def _localize_is_species(value):
    localized_value = 'Dominant' \
                      if value.lower() == 'root' \
                         else localization_map[value]
    article = 'an' if localized_value[0].lower() in 'aeiou' else 'a'

    return 'Is {} {}'.format(article, localized_value)


def _localize_is_species_class(value):
    localized_value = localization_map[value]
    article = 'an' if localized_value[0].lower() in 'aeiou' else 'a'

    return 'Is {} {}'.format(article, localized_value)


def _localize_is_enslaved(value):
        return 'Pop is enslaved' if value == 'yes' else 'Pop is NOT enslaved'


def _localize_years_passed(value):
    operator, value = _operator_and_value(value)
    return 'Number of years since game start is {} {}'.format(operator, value)


def _localize_not_years_passed(value):
    operator, value = _operator_and_value(value)
    return 'Number of years since game start is NOT {} {}'.format(operator, value)


def _localize_has_country_flag(value):
    return 'Has {} country flag'.format(value)


def _localize_has_not_country_flag(value):
    return 'Does NOT have {} country flag'.format(value)


def _localize_research_leader(values, negated=False):
    leader = 'Research Leader ({})'.format(values[0]['area'].title())
    if negated:
        leader = 'NOT ' + leader

    localized_conditions = []
    for condition in values[1:]:
        key = condition.keys()[0]
        value = condition[key]
        localized_condition = {
            'has_trait': lambda: _localize_has_expertise(value),
            'has_level': lambda: _localize_has_level(value)
        }[key]()
        localized_conditions.append(localized_condition)

    return {leader: localized_conditions}


def _localize_not_research_leader(values):
    return _localize_research_leader(values, negated=True)


def _localize_has_level(value):
    operator, level = _operator_and_value(value)
    return 'Skill level is {} {}'.format(operator, level)


def _localize_has_expertise(value):
    expertise = localization_map[value]
    if expertise.startswith('Expertise'):
        truncated = expertise.replace('Expertise: ', '')
        condition = 'Is {} Expert'.format(truncated)
    else:
        condition = 'Is {}'.format(expertise)

    return condition


def _localize_any_system_within_border(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any System within Borders': parsed_values}


def _localize_is_in_cluster(value):
    return 'Is in a {} Cluster'.format(value)


def _localize_any_country(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any Country': parsed_values}

def _localize_any_relation(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any Relation': parsed_values}

def _localize_any_owned_pop(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any empire Pop': parsed_values}

def _localize_not_any_owned_pop(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'NOT any owned Pop': parsed_values}


def _localize_any_owned_planet(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any owned Planet': parsed_values}


def _localize_any_planet(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any Planet': parsed_values}


def _localize_not_any_owned_planet(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'NOT any owned Planet': parsed_values}


def _localize_any_tile(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any Tile': parsed_values}


def _localize_has_blocker(value):
    blocker = localization_map[value]
    return 'Has {} Tile Blocker'.format(blocker)


def _localize_has_surveyed_class(value):
    return 'Has surveyed {}'.format(value)


def _localize_has_tradition(value):
    tradition = localization_map[value]
    return 'Has {} Tradition'.format(tradition)


def _localize_has_not_tradition(value):
    tradition = localization_map[value]
    return 'Does NOT have {} Tradition'.format(tradition)


def _localize_has_swapped_tradition(value):
    tradition = localization_map[value]
    return 'Has {} Swapped Tradition'.format(tradition)


def _localize_any_neighbor_country(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any Neighbor Country': parsed_values}


def _localize_has_resource(value):
    resource, amount = value[0]['type'], value[1]['amount']
    operator, amount = _operator_and_value(amount)
    localized_resource = localization_map[resource]

    return 'Has {} {} {}'.format(operator, amount, localized_resource)


def _localize_always(value):
    return 'Always' if value == 'yes' else 'Never'


def _localize_and(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'All of the following': parsed_values}


def _localize_or(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Any of the following': parsed_values}


def _localize_nor(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'None of the following': parsed_values}


def _localize_not(value):
    key = value[0].keys()[0]
    nested_value = value[0][key]

    if key == 'OR':
        # Redirect to localization of NOR:
        negation = _parse_condition({'NOR': nested_value})
    else:
        negated_key = key.replace('has_', 'has_not_') if 'has_' in key \
                      else 'not_' + key
        negated_condition = {negated_key: value[0][key]}
        negation = _parse_condition(negated_condition)

    return negation


def _localize_not_and(values):
    parsed_values = [_parse_condition(value) for value in values]
    return {'Not all of the following': parsed_values}


def _operator_and_value(data):
    if type(data) is int:
        operator = 'equal to'
        value = data
    elif type(data) is dict:
        operator = {
            '>': 'greater than',
            '<': 'less than'
        }[data.keys()[0]]
        value = data.values()[0]

    return operator, value


# NSC mod scripted triggers:
def _localize_is_playable_country(value):
    return 'Is playable Country' if value == 'yes' \
        else 'Is NOT playable Country'

# New Horizons mod scripted triggers:
def _localize_original_series_ships_era(value):
    return 'Original Series ships era' if value == 'yes' \
        else 'NOT Original Series ships era'


def _localize_motion_picture_ships_era(value):
    return 'Motion Picture ships era' if value == 'yes' \
        else 'NOT Motion Picture ships era'


def _localize_is_borg_empire(value):
    return 'Is the Borg Empire' if value == 'yes' \
        else 'Is NOT the Borg Empire'


def _localize_is_nomadic_empire(value):
    return 'Is the Nomadic Empire' if value == 'yes' \
        else 'Is NOT the Nomadic Empire'


def _localize_is_machine_cybernetic_empire(value):
    return 'Is the Machine Cybernetic Empire' if value == 'yes' \
        else 'Is NOT the Machine Cybernetic Empire'


def _localize_is_temporal_masters(value):
    return 'Is the Temporal Masters' if value == 'yes' \
        else 'Is NOT the Temporal Masters'


def _localize_is_mirror_version_empire(value):
    return 'Is a Mirror Universe Empire' if value == 'yes' \
        else 'Is NOT a Mirror Universe Empire'


def _localize_has_espionage_agency(value):
    return 'Has an Espionage Agency' if value == 'yes' \
        else 'Does NOT have an Espionage Agency'


def _localize_is_master_geneticist(value):
    return 'Has Master Geneticist Trait' if value == 'yes' \
        else 'Does NOT have Master Geneticist Trait'


def _localize_no_psionic_potential(value):
    return 'Does NOT have Psionic Potential' if value == 'yes' \
        else 'Has Psionic Potential'


def _localize_is_telepathic_empire(value):
    return 'Is a Telepathic Empire' if value == 'yes' \
        else 'Is NOT a Telepathic Empire'


def _localize_is_non_standard_colonization(value):
    return 'Is a non-standard colonization' if value == 'yes' \
        else 'Is a standard colonization'


def _localize_uses_photonic_weapons_any_torp(value):
    return 'Uses Photonic Torpedoes' if value == 'yes' \
        else 'Does NOT use Photonic Torpedoes'


def _localize_uses_plasma_weapons_any_torp(value):
    return 'Uses Plasma Torpedoes' if value == 'yes' \
        else 'Does NOT use Plasma Torpedoes'


def _localize_uses_phaser_weapons_any(value):
    return 'Uses Phasers' if value == 'yes' \
        else 'Does NOT use Phasers'


def _localize_uses_disruptor_weapons_any(value):
    return 'Uses Disruptors' if value == 'yes' \
        else 'Does NOT use Disruptors'


def _localize_uses_disruptor_weapons(value):
    return 'Uses Disruptors' if value == 'yes' \
        else 'Does NOT use Disruptors'

def _localize_uses_plasma_disruptor_weapons(value):
    return 'Uses Plasma Disruptors' if value == 'yes' \
        else 'Does NOT use Plasma Disruptors'

def _localize_uses_antiproton_weapons_any(value):
    return 'Uses Anti-Proton Weapons' if value == 'yes' \
        else 'Does NOT use Anti-Proton Weapons'

def _localize_uses_cloaks(value):
    return 'Uses Cloaking' if value == 'yes' \
        else 'Does NOT use Cloaking'

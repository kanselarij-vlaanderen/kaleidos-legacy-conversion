#!/usr/bin/python3

from .model.role import Role

MANDATARIS_TYPES = (
    'Minister',
    'Viceminister-President',
    'Minister-President',
)

def create_roles():
    roles = []
    for mt in MANDATARIS_TYPES:
        roles.append(Role(mt))
    return roles

def roles_by_label(roles):
    return {role.label: role for role in roles}

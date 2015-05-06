"""Provides utilities for manipulating schema entries"""
import copy

def make_not_empty(template_setting_dict):
    setting_dict = copy.deepcopy(template_setting_dict)
    setting_dict["empty"] = False
    return setting_dict

def make_required_full(template_setting_dict):
    setting_dict = copy.deepcopy(template_setting_dict)
    setting_dict["required"] = True
    setting_dict["empty"] = False
    return setting_dict

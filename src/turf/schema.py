"""This module contains pre-defined schema that may be useful"""
import copy

#Bugsnag 
bugsnag_api_key = {"type":"string", "regex":"^[a-f0-9]{32}$"}
bugsnag_release_stage = {"type":"string"}

#Hipchat
hipchat_api_key = {"type":"string", "regex":"^[a-zA-Z0-9]{40}$"}

uuid4 = {"type":"string", "regex":"[a-f0-9]{8}-?[a-f0-9]{4}-?4[a-f0-9]{3}-?[89ab][a-f0-9]{3}-?[a-f0-9]{12}"}

#OpsGenie
opsgenie_api_key = copy.deepcopy(uuid4)

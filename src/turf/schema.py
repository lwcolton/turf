"""This module contains pre-defined schema that may be useful"""



#Bugsnag 
bugsnag_api_key = {"type":"string", "regex":"^[a-f0-9]{32}$"}
bugsnag_release_stage = {"type":"string"}

#Hipchat
hipchat_api_key = {"type":"string", "regex":"^[a-zA-Z0-9]{40}$"}



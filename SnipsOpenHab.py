#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import configparser
from hermes_python.hermes import Hermes
from hermes_python.ffi.utils import MqttOptions
from hermes_python.ontology import *
import io
import KolfsInselAutomation

CONFIGURATION_ENCODING_FORMAT = "utf-8"
CONFIG_INI = "config.ini"

class SnipsConfigParser(configparser.SafeConfigParser):
    def to_dict(self):
        return {section : {option_name : option for option_name, option in self.items(section)} for section in self.sections()}


def read_configuration_file(configuration_file):
    try:
        with io.open(configuration_file, encoding=CONFIGURATION_ENCODING_FORMAT) as f:
            conf_parser = SnipsConfigParser()
            conf_parser.readfp(f)
            return conf_parser.to_dict()
    except (IOError, configparser.Error) as e:
        return dict()

""" Write the body of the function that will be executed once the intent is recognized. 
    In your scope, you have the following objects : 
    - intentMessage : an object that represents the recognized intent
    - hermes : an object with methods to communicate with the MQTT bus following the hermes protocol. 
    - conf : a dictionary that holds the skills parameters you defined. 
      To access global parameters use conf['global']['parameterName']. For end-user parameters use conf['secret']['parameterName'] 
     
    Refer to the documentation for further details. 
    """ 

def switch_lights_callback(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    kia = KolfsInselAutomation.KolfsInselAutomation()
    
    required_slot_question = {}
    txt = kia.SwitchLights(hermes, intentMessage, conf, required_slot_question)
    if txt == None:
        KolfsInselAutomation.ContinueSession (hermes, intentMessage, required_slot_question)
    else:
        hermes.publish_end_session(intentMessage.session_id, txt)
        
def reportOpenWindows(hermes, intentMessage):
    conf = read_configuration_file(CONFIG_INI)
    kia = KolfsInselAutomation.KolfsInselAutomation()
    
    required_slot_question = {}
    txt = kia.GetOpenWindows(hermes, intentMessage, conf, required_slot_question)
    if txt == None:
        KolfsInselAutomation.ContinueSession (hermes, intentMessage, required_slot_question)
    else:
        hermes.publish_end_session(intentMessage.session_id, txt)
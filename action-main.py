#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import toml
import KolfsInselAutomation
import configparser
import io
from CalDavCalendar import Calendar
from datetime import date, datetime, timedelta, timezone
from pytz import timezone
import calendar

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

USERNAME_INTENTS = "burkhardzeiner"
MQTT_BROKER_ADDRESS = "localhost:1883"
MQTT_USERNAME = None
MQTT_PASSWORD = None

def add_prefix(intent_name):
    return USERNAME_INTENTS + ":" + intent_name

def get_slots(data):
    slot_dict = {}
    try:
        for slot in data['slots']:
            if slot['value']['kind'] in ["InstantTime", "TimeInterval", "Duration"]:
                slot_dict[slot['slotName']] = slot['value']
            else:
                slot_dict[slot['slotName']] = slot['value']['value']
            # elif slot['value']['kind'] == "Custom":
                # slot_dict[slot['slotName']] = slot['value']['value']
    except (KeyError, TypeError, ValueError) as e:
        print("Error: ", e)
        slot_dict = {}
    return slot_dict

def getTimeRange (slotData):
    kind = slotData["kind"]
    when = None
    until = None
    if kind == "TimeInterval":        
        when = datetime.strptime(slotData["from"][:-7], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
        until = datetime.strptime(slotData["to"][:-7], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
    elif kind == "InstantTime":
        when = datetime.strptime(slotData["value"][:-7], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone('Europe/Amsterdam'))
        delta = None
        if slotData["grain"] == "Year":
            delta = timedelta(days=365)
        elif slotData["grain"] == "Quarter":
            delta = timedelta(days=365/4)
        elif slotData["grain"] == "Month":
            delta = timedelta(days=365/4)
        elif slotData["grain"] == "Week":
            end = date(year=when.year, month=when.month, day=calendar.monthrange(when.year, when.month)[1])
            delta = end - when
        elif slotData["grain"] == "Day":
            delta = timedelta(days=1)
        elif slotData["grain"] == "Hour":
            delta = timedelta(hours=1)
        elif slotData["grain"] == "Minute":
            delta = timedelta(minutes=1)
        elif slotData["grain"] == "Second":
            delta = timedelta(seconds=1)
        until = when + delta

    # TODO: precision: <“Exact”, “Approximate">

    return (when, until)

def on_message_intent(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    print (json.dumps(data))
    session_id = data['sessionId']
    intent_id = data['intent']['intentName']
    site_id = data['siteId']
    slots = get_slots (data)
    print (json.dumps(slots))

    required_slot_question = {}
    txt = "Ich verstehe dich nicht."
    shortIntent = intent_id.split(":")[1]
    print ("Short Intent: " + shortIntent)
    handledIntent = True
    if shortIntent in ["LampenAnSchalten", "LampenAusSchalten", "LichtDimmen", "lightDimPercentage"]:
        if shortIntent == "lightDimPercentage":
            custom_data = json.loads(data['customData'])
            if custom_data and 'past_intent' in custom_data.keys():
                slots.update (custom_data['slots'])
                print ("Updated slots: " + json.dumps(slots))
                (txt, required_slot_question) = kia.SwitchLights(custom_data['past_intent'], site_id, slots)
        else:
            (txt, required_slot_question) = kia.SwitchLights(intent_id, site_id, slots)
    elif shortIntent == "openWindows":
        (txt, required_slot_question) = kia.GetOpenWindows(site_id, slots)
    elif shortIntent == "goodBye":
        (txt, required_slot_question) = kia.LeaveHouse(site_id, slots)
    elif shortIntent == "goodNight":
        (txt, required_slot_question) = kia.GoodNight(site_id, slots)
    elif shortIntent == "goodMorning":
        (txt, required_slot_question) = kia.GoodMorning(site_id, slots)
    elif shortIntent == "getAppointments":
        conf = read_configuration_file(CONFIG_INI)
        try:
            (when, until) = getTimeRange(slots["date"])
            if when and until:
                calendar = Calendar(conf)
                txt = calendar.getAppointments (when, until)
                required_slot_question = None
            else:
                txt = "Zeitbereich unklar!"
        except:
            txt = "Fehler!"

    else:
        handledIntent = False
        
    if handledIntent:
        print ("Response: " + json.dumps(required_slot_question))
        if txt == None and len(required_slot_question) > 0:
            slot = next(iter(required_slot_question))
            response = required_slot_question[slot]["response"]
            intend = required_slot_question[slot]["intend"]
            custom_data = {'past_intent': intent_id, 'siteId': data['siteId'], 'slots': slots}
            dialogue(session_id, response, [add_prefix(intend)], custom_data=custom_data)
        else:
            say(session_id, txt)   
  
def say(session_id, text):
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'text': text,
                                                                         'sessionId': session_id}))


def end_session(session_id):
    mqtt_client.publish('hermes/dialogueManager/endSession', json.dumps({'sessionId': session_id}))


def dialogue(session_id, text, intent_filter, custom_data=None):
    data = {'text': text,
            'sessionId': session_id,
            'intentFilter': intent_filter}
    if custom_data:
        data['customData'] = json.dumps(custom_data)
    mqtt_client.publish('hermes/dialogueManager/continueSession', json.dumps(data))


if __name__ == "__main__":
    snips_config = toml.load('/etc/snips.toml')
    if 'mqtt' in snips_config['snips-common'].keys():
        MQTT_BROKER_ADDRESS = snips_config['snips-common']['mqtt']
    if 'mqtt_username' in snips_config['snips-common'].keys():
        MQTT_USERNAME = snips_config['snips-common']['mqtt_username']
    if 'mqtt_password' in snips_config['snips-common'].keys():
        MQTT_PASSWORD = snips_config['snips-common']['mqtt_password']

    mqtt_client = mqtt.Client()
    mqtt_client.message_callback_add('hermes/intent/#', on_message_intent)
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_BROKER_ADDRESS.split(":")[0], int(MQTT_BROKER_ADDRESS.split(":")[1]))
    mqtt_client.subscribe('hermes/intent/#')
    kia = KolfsInselAutomation.KolfsInselAutomation()
    mqtt_client.loop_forever()
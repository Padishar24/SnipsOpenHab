#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import toml
import KolfsInselAutomation

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
    if shortIntent in ["LampenAnSchalten", "LampenAusSchalten", "LichtDimmen"]:
        txt = kia.SwitchLights(intent_id, site_id, slots, required_slot_question)
    elif shortIntent == "openWindows":
        txt = kia.GetOpenWindows(site_id, slots, required_slot_question)
    elif shortIntent == "goodBye":
        txt = kia.LeaveHouse(site_id, slots, required_slot_question)
    elif shortIntent == "goodNight":
        txt = kia.GoodNight(site_id, slots, required_slot_question)
    elif shortIntent == "goodMorning":
        txt = kia.GoodMorning(site_id, slots, required_slot_question)
    else:
        handledIntent = False
        
    if handledIntent:
        print ("Response: " + json.dumps(required_slot_question))
        if txt == None:
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
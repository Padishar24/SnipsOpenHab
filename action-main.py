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
            elif slot['value']['kind'] == "Custom":
                slot_dict[slot['slotName']] = slot['value']['value']
    except (KeyError, TypeError, ValueError) as e:
        print("Error: ", e)
        slot_dict = {}
    return slot_dict


def on_message_intent(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    print (json.dumps(data))
    session_id = data['sessionId']
    intent_id = data['intent']['intentName']
    slots = get_slots (data)
    print (json.dumps(slots))

    required_slot_question = {}
    txt = "Ich verstehe dich nicht."
    # if intent_id == add_prefix("SwitchLights"):
    #     txt =   kia.SwitchLights(hermes, intentMessage, conf, required_slot_question)
    # elif intent_id == add_prefix("GetOpenWindows"):
    #     txt = kia.GetOpenWindows(hermes, intentMessage, conf, required_slot_question)
    # elif intent_id == add_prefix("LeaveHouse"):
    #     txt = kia.LeaveHouse(hermes, intentMessage, conf, required_slot_question)
    # elif intent_id == add_prefix("GoodNight"):
    #     txt = kia.GoodNight(hermes, intentMessage, conf, required_slot_question)
    # elif intent_id == add_prefix("GoodMorning"):
    #     txt = kia.GoodMorning(hermes, intentMessage, conf, required_slot_question)
    
    
    if txt == None:
        slot = next(iter(required_slot_question))
        response = required_slot_question[slot]["response"]
        intend = required_slot_question[slot]["intend"]
        custom_data = {'past_intent': intent_id, 'siteId': data['siteId'], 'slots': slots}
        dialogue(session_id, response, [add_prefix(intend)], custom_data=custom_data)
        #KolfsInselAutomation.ContinueSession (hermes, intentMessage, required_slot_question)
    else:
        say(session_id, txt)   
        #hermes.publish_end_session(intentMessage.session_id, txt)

    # if intent_id == add_prefix('newAlarm'):
    #     # create new alarm with the given properties
    #     slots = get_slots(data)
    #     say(session_id, alarmclock.new_alarm(slots, data['siteId']))

    # elif intent_id == add_prefix('getAlarms'):
    #     # say alarms with the given properties
    #     slots = get_slots(data)
    #     say(session_id, alarmclock.get_alarms(slots, data['siteId']))

    # elif intent_id == add_prefix('getNextAlarm'):
    #     # say next alarm
    #     slots = get_slots(data)
    #     say(session_id, alarmclock.get_next_alarm(slots, data['siteId']))

    # elif intent_id == add_prefix('getMissedAlarms'):
    #     # say missed alarms with the given properties
    #     slots = get_slots(data)
    #     say(session_id, alarmclock.get_missed_alarms(slots, data['siteId']))

    # elif intent_id == add_prefix('deleteAlarms'):
    #     # delete alarms with the given properties
    #     slots = get_slots(data)
    #     alarms, response = alarmclock.delete_alarms_try(slots, data['siteId'])
    #     if alarms:
    #         custom_data = {'past_intent': intent_id,
    #                        'siteId': data['siteId'],
    #                        'slots': slots}
    #         dialogue(session_id, response, [add_prefix('confirmAlarm')], custom_data=custom_data)
    #     else:
    #         say(session_id, response)

    # elif intent_id == add_prefix('confirmAlarm'):
    #     custom_data = json.loads(data['customData'])
    #     if custom_data and 'past_intent' in custom_data.keys():
    #         slots = get_slots(data)
    #         if 'answer' in slots.keys() and \
    #                 slots['answer'] == "yes" and \
    #                 custom_data['past_intent'] == add_prefix('deleteAlarms'):
    #             response = alarmclock.delete_alarms(custom_data['slots'], custom_data['siteId'])
    #             say(session_id, response)
    #         else:
    #             end_session(session_id)
    #         alarmclock.temp_memory[data['siteId']] = None

    # elif intent_id == add_prefix('answerAlarm'):
    #     slots = get_slots(data)
    #     say(session_id, alarmclock.answer_alarm(slots, data['siteId']))
  

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
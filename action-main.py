#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import json
import toml
import KolfsInselAutomation
from CalDavCalendar import Calendar
from Tools import IntentMsg, getTimeRange, get_slots, read_configuration_file
import datetime

USERNAME_INTENTS = "burkhardzeiner"
MQTT_BROKER_ADDRESS = "localhost:1883"
MQTT_USERNAME = None
MQTT_PASSWORD = None

def add_prefix(intent_name):
    return USERNAME_INTENTS + ":" + intent_name

def on_message_intent(client, userdata, msg):
    intentMsg = IntentMsg(msg)

    required_slot_question = {}
    txt = "Ich verstehe dich nicht."
    shortIntent = intentMsg.intent_id.split(":")[1]
    print ("Short Intent: " + shortIntent)
    handledIntent = True
    if shortIntent in ["LampenAnSchalten", "LampenAusSchalten", "LichtDimmen", "lightDimPercentage"]:
        if shortIntent == "lightDimPercentage":
            if intentMsg.custom_data and 'past_intent' in intentMsg.custom_data.keys():
                intentMsg.slots.update (intentMsg.custom_data['slots'])
                (txt, required_slot_question) = kia.SwitchLights(intentMsg.custom_data['past_intent'], intentMsg.site_id, intentMsg.slots)
        else:
            (txt, required_slot_question) = kia.SwitchLights(intentMsg.intent_id, intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "openWindows":
        (txt, required_slot_question) = kia.GetOpenWindows(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodBye":
        (txt, required_slot_question) = kia.LeaveHouse(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodNight":
        (txt, required_slot_question) = kia.GoodNight(intentMsg.site_id, intentMsg.slots)
    elif shortIntent == "goodMorning":
        (txt, required_slot_question) = kia.GoodMorning(intentMsg.site_id, intentMsg.slots)

        if txt:
            calendar = Calendar(intentMsg.config)
            
            today = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time())
            tomorrow = today + datetime.timedelta(days=1)
            appointmentsInSpeak = calendar.getAppointments (today, tomorrow, includeSpeakTag=False)

            if appointmentsInSpeak:
                txt = "<speak><s>" + txt + "</s><p>Folgende Termine stehen heute an:</p>" + appointmentsInSpeak + "</speak>"

    elif shortIntent == "getAppointments":
        try:
            (when, until) = getTimeRange(intentMsg.slots["date"])
            if when and until:
                calendar = Calendar(intentMsg.config)
                txt = calendar.getAppointments (when, until)
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
            custom_data = {'past_intent': intentMsg.intent_id, 'siteId': intentMsg.site_id, 'slots': intentMsg.slots}
            dialogue(intentMsg.session_id, response, [add_prefix(intend)], custom_data=custom_data)
        else:
            say(intentMsg.session_id, txt)   
  
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

def onDialogSessionStarted(client, userdata, msg):
    print ("**** SESSION START DETECTED ****")
    pass

def onDialogSessionEnded(client, userdata, msg):
    print ("**** SESSION END DETECTED ****")
    pass


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
    mqtt_client.message_callback_add ('hermes/dialogueManager/sessionStarted', onDialogSessionStarted)
    mqtt_client.message_callback_add ('hermes/dialogueManager/sessionEnded', onDialogSessionEnded)
    mqtt_client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    mqtt_client.connect(MQTT_BROKER_ADDRESS.split(":")[0], int(MQTT_BROKER_ADDRESS.split(":")[1]))
    mqtt_client.subscribe('hermes/intent/#')
    mqtt_client.subscribe ('hermes/dialogueManager/sessionStarted')
    mqtt_client.subscribe ('hermes/dialogueManager/sessionEnded')
    kia = KolfsInselAutomation.KolfsInselAutomation()
    mqtt_client.loop_forever()
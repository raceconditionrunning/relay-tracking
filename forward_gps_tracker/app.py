import argparse
import datetime
import json
import os
import time
import ssl
import gps_tracker
import paho.mqtt.client as mqtt


def format_location_frame(frame, tracker_name, battery_level=None):
    formatted = {
    "_type": "location",
        "t": "u",
        "acc": frame.precision,
                 "lat": frame.lat,
                 "lon": frame.lng,
                 "tid": tracker_name,
    "tst": int(frame.datetime.timestamp())
                }

    if battery_level:
        formatted["batt"] = battery_level
        formatted["bs"] = 1
    return formatted


def forward_tracker_data(client, mqtt_client, check_interval=30, name=None, topic=None):
    trackers = client.get_devices(kind="tracker")
    last_check_time = datetime.datetime.now() - datetime.timedelta(seconds=600)
    i = 0
    should_break = False
    already_sent = []
    while True:
        for tracker in trackers:
            if should_break:
                break
            try:
                # Tracker may go some time without connecting, so we'll look back a bit for slightly stale but new-to-us
                # data
                locations = client.get_locations(tracker, not_before=last_check_time - datetime.timedelta(minutes=15), max_count=10)
            except gps_tracker.client.exceptions.ApiConnectionError as e:
                print(e)
                # Back off a bit and recreate the connection
                time.sleep(check_interval * 2)
                client = gps_tracker.Client(cfg)
                should_break = True
                continue
            for location in locations:
                if location.uuid in already_sent:
                    continue
                already_sent.append(location.uuid)
                frame = format_location_frame(location, tracker.name, tracker.tracker_status.battery)
                print(location)
                res = mqtt_client.publish(f"{topic}/{tracker.name}", payload=json.dumps(frame))
                print(frame)
                print(res)
        if should_break:
            should_break = False
            continue
        last_check_time = datetime.datetime.now()
        if len(already_sent) > 500:
            already_sent = already_sent[250:]
        print("Done at ", last_check_time.isoformat())
        mqtt_client.loop()
        time.sleep(30)
        i += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("username")
    parser.add_argument("password")
    parser.add_argument("mqtt_host")
    parser.add_argument("mqtt_username")
    parser.add_argument("mqtt_password")
    parser.add_argument("--mqtt-topic")
    parser.add_argument("--mqtt-port", default=8883, type=int)
    parser.add_argument("--device-name")
    parser.add_argument("--check-interval", default=30, type=int)
    parser.add_argument("--tls", action="store_true")
    args = parser.parse_args()
    print(args)

    cfg = gps_tracker.Config(username=args.username, password=args.password)
    client = gps_tracker.Client(cfg)
    mqtt_client = mqtt.Client(f"forward_gps_tracker{os.getpid()}", protocol=mqtt.MQTTv5)
    mqtt_client.username_pw_set(args.mqtt_username, args.mqtt_password)
    if args.tls:
        mqtt_client.tls_set(cert_reqs=ssl.CERT_REQUIRED)
    mqtt_client.connect(host=args.mqtt_host, port=args.mqtt_port)
    forward_tracker_data(client, mqtt_client, check_interval=args.check_interval, topic=args.mqtt_topic)

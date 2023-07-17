FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./requirements.txt

RUN pip install -r requirements.txt

COPY app.py ./

CMD exec python app.py $FORWARD_USERNAME $FORWARD_PASSWORD $FORWARD_MQTT_HOST $FORWARD_MQTT_USERNAME $FORWARD_MQTT_PASSWORD --mqtt-port $FORWARD_MQTT_PORT --mqtt-topic $FORWARD_MQTT_TOPIC $USE_TLS_ARG
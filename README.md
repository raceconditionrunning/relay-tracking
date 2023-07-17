# Relay Tracking

Location tracking server stack configured for live-tracking runners during a road relay. Originally set up
for Race Condition Running's 2023 Ragnar Northwest Passage team.

Consists of:

* [OwnTracks recorder](https://github.com/owntracks/recorder): lightweight location database that talks to clients over MQTT/HTTP/WebSockets
* [Mosquitto MQTT broker](https://mosquitto.org/) (server): manages long-lived MQTT connections 
* `forward_gps_tracker`: a small shim for forwarding location data from an [Invoxia Cellular GPS tracker](https://www.invoxia.com/en-US/product/gps-tracker) to the broker (in case you have runners who don't want to use their phone).

## Usage

If you have a tracker and plan to use the forwarder, build the forwarder image.

    sudo docker build -t forward-gps-tracker .

You should already have SSL certs for the domain you plan to host the server on.
Create a `.env` file in this directory and tell the containers what credentials to use.

```
OTR_PASS=x
CERT_PATH="/etc/letsencrypt/live/yourhost.com"
FORWARD_USERNAME=x
FORWARD_PASSWORD=x
FORWARD_MQTT_USERNAME=x
FORWARD_MQTT_PASSWORD=x
```

Run the three containers together using the included Docker Compose config:

    sudo docker compose up

Use `sudo docker-compose --profile forwarder up` if you're using the forwarder.

Configure the OwnTracks recorder password with the MQTT broker now that the containers are up:

    sudo docker exec -i mosquitto mosquitto_passwd -b /mosquitto/config/password_file owntracks $password

Make sure port 8883 is open for the MQTT broker.

Further configuration depends on your relay set up. Our configuration from a Ragnar is included in `scripts/make_configs.sh`.
It'll set up accounts and credentials for runners and generate configuration files for the OwnTracks mobile clients. You can also
preload these configurations with exchange locations by creating the per-runner JSON files consisting of arrays of waypoints. Here's an example
waypoint:

```
{
  "type": "_waypoint",
  "desc": "Exchange 0",
  "rad": 100,
  "lat": 49.001428375,
  "lon": -122.753892034
}
```

### HTTP API

OwnTracks recorder includes an HTTP and WebSocket server which makes building web clients simple ([see our Ragnar NWP map](https://github.com/raceconditionrunning/raceconditionrunning.github.io/blob/main/pages/ragnar-23.html)). You should expose
the parts of the server you need using a reverse proxy like nginx:

```
server {
    include snippets/listen-https.conf;
    server_name yourhost.com;
    root /var/www/yourhost.com;

    # ... SSL config ...

    location / {
        # Includes basic table views and historical maps of locations. Expose with caution!
        proxy_pass http://localhost:8083;
    }

    # Proxy and upgrade WebSocket connection. Live feed of location events.
    location /ws {
            proxy_pass      http://localhost:8083;
            proxy_http_version  1.1;
            proxy_set_header    Upgrade $http_upgrade;
            proxy_set_header    Connection "upgrade";
            proxy_set_header    Host $host;
            proxy_set_header    X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # OwnTracks Recorder Views (requires /view, /static, /utils)
    location /view/ {
         proxy_buffering         off;            # Chrome
         proxy_pass              http://localhost:8083/view/;
         proxy_http_version      1.1;
         proxy_set_header        Host $host;
         proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header        X-Real-IP $remote_addr;
    }
    
    location /static/ {
         proxy_pass              http://localhost:8083/static/;
         proxy_http_version      1.1;
         proxy_set_header        Host $host;
         proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header        X-Real-IP $remote_addr;
    }

    location /utils/ {
         proxy_pass              http://localhost:8083/utils/;
         proxy_http_version      1.1;
         proxy_set_header        Host $host;
         proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header        X-Real-IP $remote_addr;
    }

    # HTTP read API. You can wrap this in basic auth if you want to limit reading, but really 
    # you should configure views for your runners and only expose them.
    location /api/0/ {
         proxy_pass              http://localhost:8083/api/0/;
         proxy_http_version      1.1;
         proxy_set_header        Host $host;
         proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
         proxy_set_header        X-Real-IP $remote_addr;
    }

    # HTTP write API. Uses Basic Auth to limit clients to only publish their
    # own info.
    location /pub {        
        auth_basic "OwnTracks pub";
        auth_basic_user_file /etc/nginx/owntracks.htpasswd;
        proxy_pass http://localhost:8083/pub;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Limit-U $remote_user;
    }

}
```

### Debugging

Take a look at container std-out logs:

    sudo docker logs --follow forward-gpstracker

Listen for MQTT messages:

    sudo docker exec -i mosquitto mosquitto_sub  -h localhost -p 1883 -t owntracks/runner2/phone
#!/usr/bin/env bash
set -ex

if [ $# -lt 2 ]; then
  echo 1>&2 "$0: not enough arguments"
  exit 2
fi

# MQTT hostname (just host, no protocol)
host=$1
# Same password for all clients to make it easier for them to switch identities (e.g. if people ad hoc swap assignments)
password=$2

runners=('runnertracker' 'runner1' 'runner2' 'runner3' 'runner4' 'runner5' 'runner6' 'runner7' 'runner8' 'runner9' 'runner10' 'runner11' 'runner12')
devices=('tracker' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone' 'phone')

rm -rf client_configs; mkdir client_configs
sudo rm -f volumes/mosquitto/config/password_file; sudo touch volumes/mosquitto/config/password_file
sudo docker exec -i mosquitto mosquitto_passwd -b /mosquitto/config/password_file owntracks $password

for ((i=0; i<${#runners[@]}; i++)); do
  # Friends need to be configured manually in HTTP mode. We'll use MQTT instead but leaving this
  # dead code here in case we want to switch back.
  #other_runners=("${runners[@]:0:i}" "${runners[@]:i+1}")
  #other_devices=("${devices[@]:0:i}" "${devices[@]:i+1}")

  #friends="\"${other_runners[0]}/${other_devices[0]}\""
  # Iterate over the indices
  #for ((j=1; j<${#other_runners[@]}; j++)); do
  #  friends+=", \"${other_runners[j]}/${other_devices[j]}\""
  #done

  #echo $friends
  #docker exec -i owntracks-recorder ocat --load=friends <<EOF
  #${runners[i]}-${devices[i]} [ ${friends} ]
  #EOF
  # To check if it worked: sudo docker exec -it owntracks-recorder ocat --dump=friends

  sudo docker exec -i mosquitto mosquitto_passwd -b /mosquitto/config/password_file ${runners[i]} $password

  # If you want to allow HTTP clients, you'll want to wrap OwnTracks recorder's HTTP end point with a
  # reverse proxy and use at least Basic Auth to limit publishers to the same extent as the MQTT endpoint.
  # sudo htpasswd -b /etc/nginx/owntracks.htpasswd ${runners[i]} $password
  #http_config=$(jo -p _type='configuration' \
  #  auth=true \
  #  username=${runners[i]} \
  #  password=${password} \
  #  usePassword=true \
  #  url="https://${host}/pub" \
  #  deviceId=${devices[i]} \
  #  mode=3 \
  #  tid="${i}" \
  #  monitoring=0 \
  #  downgrade=20
  #)

  mqtt_config=$(jo -p _type='configuration' \
    auth=true \
    username=${runners[i]} \
    password="${password}" \
    usePassword=true \
    host="${host}" \
    port=8883 \
    tls=true \
    deviceId=${devices[i]} \
    mode=0 \
    tid="${i}" \
    monitoring=1 \
    downgrade=20 \
    locatorDisplacement=200 \
    locatorInterval=180 \
    cmd=1 \
    waypoints="$(cat runner${i}_waypoints.json)"
  )
  # downgrade = battery level below which to downgrade monitoring from move mode
  # Android client needs the file
  echo $mqtt_config > "client_configs/${runners[i]}.otrc"
  echo "${runners[i]}" >> client_configs/urls.txt
  # There urls will be too long to parse on iOS if they include waypoints
  echo "owntracks:///config?inline=$(openssl enc -a -A -in client_configs/${runners[i]}.otrc)" >> client_configs/urls.txt
  # More reliable config method. There's a 3000 char upper limit on QR codes but you shouldn't have that many waypoints anyways
  qrencode -o client_configs/${runners[i]}.png $(cat client_configs/${runners[i]}_url.txt)
done


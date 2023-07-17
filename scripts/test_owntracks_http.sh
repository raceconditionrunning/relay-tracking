#!/usr/bin/env bash
set -ex

if [ $# -lt 2 ]; then
  echo 1>&2 "$0: not enough arguments"
  exit 2
fi

user='runner1'
device='phone'
hostname=$1
password=$2

payload="{\"_type\":\"location\",
   \"t\":\"u\",
   \"batt\":11,
   \"bs\":1,
   \"acc\":200,
   \"lat\":49.00167450044327,
   \"lon\":-122.75169128904402,
   \"tid\":\"1\",
   \"tst\":\"$(date +%s)\",
   \"topic\":\"owntracks/${user}/${device}\"
   }"

payload=$(jo _type="location" \
   t="u" \
   batt=11 \
   bs=1 \
   acc=200 \
   lat=49.00167450044327 \
   lon=-122.75169128904402 \
   -s tid="1" \
   tst="$(date +%s)" \
   topic="owntracks/${user}/${device}")

echo $payload
curl -u "${user}:${password}" --data "${payload}" https://${hostname}/pub?u=${user}&d=${device}
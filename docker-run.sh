#!/bin/sh
docker run -it \
  -p 45678:45678 \
  -v .:/host/ \
  dddpaul/google-drive-permission-reset \
  --auth-port=45678 \
  --credentials-path /host/credentials.json \
  --token-path /host/token.pickle \
  "$@"

#!/bin/bash

docker run \
    -d \
    --name notifications-service \
    --network labassignement \
    dclandau/cec-notifications-service --secret-key QJUHsPhnA0eiqHuJqsPgzhDozYO4f1zh --external-ip localhost
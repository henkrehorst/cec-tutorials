docker build -t notification-sender -f Dockerfile .
docker run --rm \
 --name notification-sender\
 -v ./assignment:/usr/src/app/assignment \
  --network labassignement\
   notification-sender
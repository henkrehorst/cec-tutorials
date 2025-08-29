# Overview

This tutorial aims to show how distributed systems communicate with one
another through publish/subscribe communication protocols. We will specifically
use Kafka, which is a common message broker implementations used in the
industry due to its scalability, fault tolerance, availability, etc...

# Kafka Credentials

A development Kafka cluster is setup to which we will connect to throughout
this tutorial. To access the cluster, each student should have been provided a
OneDrive folder with the required credentials. We will now upload the folder to
our respective VMs.

## Session 1

Let's start with downloading our folders into a known location in our
computers. This part of the tutorial will depend on which ssh client you are
using.

### openssh

If running an openssh client, you can run this command to copy a local file
into your VM (don't forget to change the different parameters):

```bash
scp -r -i <your-pem-file> <local-credentials-directory> ubuntu@<your-VMs-public-IP>:<kafka-tutorials-directory>

# E.g. scp -r -i ../client50/ssh_key_50 ../client50 ubuntu@13.48.5.125:/home/ubuntu/cc-2023-tutorials/kafka/auth
```

### Other clients

If running other clients they might have a specific way of allowing files to be
transferred. If in doubt, raise your hand.

# Simple Producer Consumer

We will now create a simple data producer, that will write messages/events into
our kafka topic. At the same time, we will start a simple consumer that will
read the messages that are being published. These are the simples interactions
2 clients may have with the Kafka cluster. 

The producer, 
```python
# simple_producer_consumer/producer.py
import click

from confluent_kafka import Producer

p = Producer({
    'bootstrap.servers': '13.60.146.188:19093,13.60.146.188:29093,13.60.146.188:39093',
    'security.protocol': 'SSL',
    'ssl.ca.location': './auth/ca.crt',
    'ssl.keystore.location': './auth/kafka.keystore.pkcs12',
    'ssl.keystore.password': 'cc2023',
    'ssl.endpoint.identification.algorithm': 'none',
})

@click.command()
@click.argument('topic')
def produce(topic: str): 
    while True: 
        message = input()
        p.produce(topic, key="1", value=message.encode('utf-8'))
        p.flush()


produce()
```
is configured, then reads in an argument passed in as the topic. The topic you will
subscribe to is your client `id`, e.g., in my case it is `client58`. It then
starts a loop where it asks for a user's input, and sends the message to kafka.

With regards to the consumer,
```python
# simple_producer_consumer/consumer.py
import signal
import click 
import random

from confluent_kafka import Consumer


def signal_handler(sig, frame):
    print('EXITING SAFELY!')
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)

c = Consumer({
    'bootstrap.servers': '13.60.146.188:19093,13.60.146.188:29093,13.60.146.188:39093',
    'group.id': f"{random.random()}",
    'auto.offset.reset': 'latest',
    'enable.auto.commit': 'true',
    'security.protocol': 'SSL',
    'ssl.ca.location': './auth/ca.crt',
    'ssl.keystore.location': './auth/kafka.keystore.pkcs12',
    'ssl.keystore.password': 'cc2023',
    'ssl.endpoint.identification.algorithm': 'none',
})

@click.command()
@click.argument('topic')
def consume(topic: str): 
    c.subscribe(
        [topic], 
        on_assign=lambda _, p_list: print(p_list)
    )

    num_events = 0
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        num_events += 1
        if num_events % 1000 == 0:
            print(num_events)
        print(msg.value())

consume()
```
it is first configured, then receives as input the topic to subscribe to.
This must be the same as the topic passed to the producer. It then enters an
infinite loop that polls to check whether there are any messages to be
consumed, and if so prints them to standard output. 

## Demo

Start an ssh session with your vm. Change directory into the tutorial
repository's directory, followed by: 
```bash
cd kafka
```

Let's make sure the repository is up to date:
```bash
git pull
```

Start by building the image:
```bash
docker build -t tkafka/simple simple_producer_consumer
```

We may now start our consumer. Don't forget to change the topic `<topic>`
argument: 
```bash
docker run \
    --rm \
    -d \
    --name simple_consumer \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/simple consumer.py "<topic>"
```

We can now also run our producer, and write messages toward our topic. Also
don't forget to change the `<topic>` field:

> Note: 
> Because our producer is requesting user input, we are running our producer in
> interactive mode with the options `-it`

```bash
docker run \
    --rm \
    -it \
    --name simple_producer \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/simple producer.py "<topic>"
```

check the output of the consumer: 
```bash
docker logs -f simple_consumer
```
You should see the messages we just wrote with the producer.

We can terminate our `simple_consumer` now: 
```bash
docker stop simple_consumer
```

# Commit Offsets

Our goal now is to understand the kafka's commit offsets. This functionality
exists in Kafka, so it can track where a client left off the last time it
connected to a topic.

The identifier kafka uses to locate a client's offset in each topic
partition is the `group.id` configuration parameter.

There are 2 behaviours. If Kafka finds an offset for the client + the topic it
is consuming from, then it starts where it last left off. Otherwise, its
behaviour is determined by the `auto.offset.reset` parameter.
`auto.offset.reset` can be set to `latest` or `earliest`:

- `latest` will ignore any messages published before the time it connected, and
  consume only new messages
- `earliest` will start consuming from the oldest message in each partition of
  the topic.

> Important! 
>
> What is described in this section will be important if you have to delete
> previous messages published into the kafka topic. Kafka does not allow
> deleting any of the messages you published, and therefore you have to rely on
> this behaviour to start consuming only what will be published from that
> moment forward. 

## Demo

To demonstrate this functionality, we will start by creating 2 different
consumers that have never read from the topic before. Their functionality will
be similar to the last consumer's, but we will change the `auto.offset.reset`
parameter:
```bash
docker build -t tkafka/commit_offsets commit_offsets

docker run \
    --rm \
    -d \
    --name consumer_earliest \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/commit_offsets consumer.py "<topic>" "earliest"

docker run \
    --rm \
    -d \
    --name consumer_latest \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/commit_offsets consumer.py "<topic>" "latest"
```

If we now look at the logs of each consumer we will see that the consumer
defined with `latest` will not print the messages your wrote on the first part
of the assignment, whereas the consumer with the `earliest` value will print
everything from the beginning: 

> Note:
> Wait until you at least see the on_assign callback printing the partitions
> assigned to each consumer before closing the logs.

```bash
docker logs -f consumer_earliest
```

```bash
docker logs -f consumer_latest
```

We can now delete the 2 consumers we have created: 
```bash
docker stop consumer_earliest consumer_latest
```

We now want to understand how the `group.id` can be used to save a consumer's
position in each topic partition. With each message we read from our topic, we
will pretend our consumer has to make sure it is storing the data in a database
before it commits the offset to Kafka. This is represented with a short sleep:
```python
# commit_offsets/consumer_commit.py
# ...
        print(msg.value())
        store_data()
        c.commit(message=msg)
        print("Message committed")
# ... 
```

We will now start our consumer which should start slowly printing each message
and the other debug information (don't forget to change the `<topic>` and
`<unique-group-id>`):
```bash
docker run \
    --rm \
    -d \
    --name consumer_commit \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/commit_offsets consumer_commit.py "<topic>" "<unique-group-id>"

docker logs -f consumer_commit
```

Stop the consumer as it between the "Start Storing" and the "End Storing" messages.
```bash
docker stop consumer_commit
```

We will now restart the consumer:
```bash
docker run \
    --rm \
    -d \
    --name consumer_commit \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/commit_offsets consumer_commit.py "<topic>" "<unique-group-id>"

docker logs -f consumer_commit
```

We expect that the consumer re-reads the same message where it was interrupted
before commiting the message. 

We can now delete the consumer: 
```bash
docker stop consumer_commit
```

# Consumer Group

A consumer group is an abstraction kafka provides that allows parallelizing the
data consumption between the consumers belonging to the same group. The effect
is an increase of the rate at which data is consumed.

But how do multiple consumers read from the same topic, without reading
overlapping messages? What enables this behaviour is Kafka's topic
partitioning, wherein a single topic can have multiple partitions, e.g., in our
case, each of our topics has 16 partitions. 

To guarantee all messages produced to the topic are read by the group, each
partition has to be assigned to a single consumer in a group. When there are
multiple active consumer's belonging to the same group, kafka attempts to
balance out the load between the different consumers by assigning them an equal
amount of partitions. E.g. if we have 2 consumers in our group reading from our
topic, then each consumer will be assigned 8 partitions.

Partitions are also the unit where kafka guarantees message ordering. What
determines which partition a message will be assigned to is a message's key. If
2 messages have the same partition key, then it is guaranteed they will be sent
to the same partition. In our assignment, the key of all messages for an
experiment is the experiment's identifier, so as to make sure that the messages
will be consumed in the same order as they were produced. If on the other hand
the messages were published into different partitions, there would be no
guarantee that the messages would be read in the correct order. 

The following figure illustrates Kafka's publish/subscribe communication model
for a topic with 4 partitions: 
![Kafka Architecture](https://github.com/landaudiogo/cc-2023-tutorials/assets/26680755/d51aa0bc-7a74-4cac-9d78-6d1590d3de91)

## Demo

We will make use of our producer from before with the added code that includes
a key on each message. The key value increments everytime we write a new
message to try and make it go to different partitions. 

```python
# consumer_group/producer.py
# ...
        p.produce(topic, key=f"{i}", value=message.encode('utf-8'))
        p.flush()
        i+=1
# ...
```

We will now start 2 consumers with `"group.id": "<any-group-id>"`,
meaning they will belong to the same consumer group (remember to change
`<any-group-id>` by an identifier of your choosing):

```bash
docker build -t tkafka/consumer_group consumer_group

docker run \
    --rm \
    -d \
    --name consumer_1 \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/consumer_group consumer.py "<topic>" "<any-group-id>"

docker run \
    --rm \
    -d \
    --name consumer_2 \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/consumer_group consumer.py "<topic>" "<any-group-id>"
```

If we now check their logs, we may see that after the partitions have been
assigned, each consumer has been assigned 8 of the 16 partitions, without any
overlap.

```bash
docker logs -f consumer_1 # wait for the printed partition assignment
docker logs -f consumer_2 # wait for the printed partition assignment
```

We will now start our producer which will write data to the partitions "at
random":
```bash
docker run \
    --rm \
    -it \
    --name producer \
    -v "$(pwd)/auth":/usr/src/app/auth \
    tkafka/consumer_group producer.py "<topic>"
```

We expect that as you write messages either `consumer_1` or `consumer_2` is
getting them, but NEVER BOTH.

After writing the messages, check each consumer's output:
```bash
docker logs -f consumer_1
```
```bash
docker logs -f consumer_2
```
As expected each message was directed to only one of our consumers in our
group.

We can now stop our consumers:
```bash
docker stop consumer_1 consumer_2
```

## Session 2

The goal of this session is to show you how to leverage the tools we provide you, so you can test the systems you are developing effectively. 

The experiment-producer is the component you use to generate the events that your service has to consume. By passing specific parameters to the experiment-producer you will be able to vary the load applied to your service, and cross-reference the data it generates with the data you are computing and storing. 

### Load Variability

There are multiple ways you could use the experiment-producer to vary the load, however, the most efficient way is to use the integrated `--config-file <file>` parameter. This file, allows you to specify multiple experiments with varying configurations. For example, the following configuration starts 2 experiments, where the first will start immediately after the experiment-producer starts, and the second will start 30 seconds later: 

```
# loads/2.json
[
    {
        "start_time": 0,
        "researcher": "d.landau@uu.nl",
        "num_sensors": 10,
        "sample_rate": 1000,
        "start_temperature": 0,
        "stabilization_samples": 10,
        "carry_out_samples": 50,
        "temp_range": {
            "lower_threshold": 100,
            "upper_threshold": 150
        }
    },
    {
        "start_time": 30,
        "researcher": "d.landau@uu.nl",
        "num_sensors": 8,
        "sample_rate": 200,
        "start_temperature": 0,
        "stabilization_samples": 10,
        "carry_out_samples": 80,
        "temp_range": {
            "lower_threshold": 10,
            "upper_threshold": 20
        }
    }
]
```

You can estimate the load each experiment will generate in events/s using the following calculation `num_sensors * (1000/sample_rate)`. And the estimated duration of the experiment can be calculated with `stabilization_samples / (1000/sample_rate) + carry_out_sample / (1000/sample_rate)`. As such, for the same example as the one above, the production rate of the first experiment is `10 * (1000/1000) =10 events/s`, and it will run for `10 / (1000/1000) + 50 / (1000/1000) = 60 s`. The second experiment has a production rate of `8 * (1000/200) = 40 events/s` and will run for approximately `10 / (1000/200) + 80 / (1000/200) = 18s`.

Given that the second experiment starts before the first experiment terminates, there will be some overlap between both experiments. As such, between seconds 30-48, the total production rate is the combination of the production rate of both experiments, i.e., `10 + 40 = 50 events/s`.

Let's put this to the test. Create a network, start the production-rate visualiser, and make sure it is included in the network we just created:
```bash
docker network create producer
docker run --network producer -d --rm --name production-rate -it -p 3005:8501 --rm --name production-rate dclandau/cec-production-rate --producer-connection producer:3001
```

Note that we also mapped the VM's port 3005 with the container's port 8501. If you now open your browser on `http://<your-vm-ip>:3005` you should see an empty graph. To start observing data in the graph displayed on the browser, start the producer as follows (please change the parameterised `<auth-dir>` and `<topic>` in the command): 
```bash
docker run --rm --name producer -v <auth-dir>:/experiment-producer/auth -v ./kafka/loads/2.json:/config.json -it --network producer dclandau/cec-experiment-producer -b kafka1.dlandau.nl:19092 --config-file /config.json --topic <topic>
```
The graph should now display the rate at which data is produced in `events/s`.

Let's run a similar configuration, but now we will start a 3rd experiment 45 seconds after we have started the producer:
```
# loads/3.json
[
    {
        "start_time": 0,
        "researcher": "d.landau@uu.nl",
        "num_sensors": 10,
        "sample_rate": 1000,
        "start_temperature": 0,
        "stabilization_samples": 10,
        "carry_out_samples": 50,
        "temp_range": {
            "lower_threshold": 100,
            "upper_threshold": 150
        }
    },
    {
        "start_time": 30,
        "researcher": "d.landau@uu.nl",
        "num_sensors": 8,
        "sample_rate": 200,
        "start_temperature": 0,
        "stabilization_samples": 10,
        "carry_out_samples": 80,
        "temp_range": {
            "lower_threshold": 10,
            "upper_threshold": 20
        }
    },
    {
        "start_time": 45,
        "researcher": "d.landau@uu.nl",
        "num_sensors": 20,
        "sample_rate": 500,
        "start_temperature": 0,
        "stabilization_samples": 5,
        "carry_out_samples": 50,
        "temp_range": {
            "lower_threshold": 100,
            "upper_threshold": 150
        }
    }
]
```

Make sure you refresh your browser. After doing so, start the producer making sure that you change the configuration file to `./kafka/loads/3.json`. 
```bash
docker run --rm --name producer -v <auth-dir>:/experiment-producer/auth -v ./kafka/loads/3.json:/config.json -it --network producer dclandau/cec-experiment-producer -b kafka1.dlandau.nl:19092 --config-file /config.json --topic <topic>
```

You should now see that up until the 45th second, the graph looks very similar, however, since we have added another experiment starting at second 45, the remainder of the production rate will now also include this new experiment.

### Data Consistency

# Lab Assignment

The goal of this assignment is to learn how to deploy the `experiment_producer`
service, and deserialize the data it produces.

For this lab assignment, you will have to: 

- Adapt the `start-producer.sh` script to start 3 instances of the
  `experiment-producer` **CONCURRENTLY**. 
  > Tip: 
  > Consider creating a bash for loop around the command that instantiates the
  > experiment-producer container.
- Create a single consumer that deserializes all the messages produced by the
  experiment-producer instances. When reading a message produced into the
  topic, your consumer should, first print the message header `record_name`
  followed by the deserialized messages. 
  E.g.: 
  ```txt
  sensor_temperature_measured
  {'experiment': '577cb8c3-0c81-456e-9314-349937ca08a9', 'sensor': '9a8d38b9-35d2-4436-9cb8-0185edbc077c', 'measurement_id': 'fc6e5b2b-ec78-4bbd-bab7-94c24907d1cf', 'timestamp': 1694266072.336535, 'temperature': 29.995697021484375, 'measurement_hash': 'Xf0r67teLs16dD12.SmEXcqiXtJPwJ8CCTXF7gMfXKeWAr/3b7jisYBeuaAvdxYNDc7yIpbXKW73QMNguxCu0Q4Do7cPwL8W//6qp0sO682sHZ6xWrIlssGhTOjK3TDXlew4x1pbaVhPNq1LuLuRDq/AQHJZEsXqT2PYebydv16tLvlAwbAR9VkAi1DmI4SwIhRVyGk6EkhMqMbby8BWQsrelf4adUy9CuZ91KORBs6tItiHlBBeWy87V3xfY+nHR+Tn5JjQW7dg9IoAZCqBAa5ZK1a5KhPWHySpvgqurGd0P'}
  experiment_terminated
  {'experiment': '577cb8c3-0c81-456e-9314-349937ca08a9', 'timestamp': 1694266072.6484454}
  ```
  > This document shows a simple python example of how serialization and
  > deserialization works in Python:
  > https://avro.apache.org/docs/1.11.1/getting-started-python/

  The data published by the `experiment_producer` is in the avro format. So I
  would recommend you read the document linked above. Make sure you also print
  the message header `record_name` before printing each message, as shown in
  the output above.
- You may create the consumer in any programming language, as long as it has
  support for kafka consumers and apache avro. E.g. Because rust has a rdkafka
  and apache avro library, the experiment-producer was developed in rust;
  Python also has libraries for both, and for the output illustrated above, I
  used Python.
- Try changing the parameters passed into the `experiment-producer` such as the
  duration, sample-rate, stabilization-samples, carry-out-samples, etc...
  To see the available options, run the script with the `--help` parameter.
  E.g.:
  ```
  start-producer.sh auth topic brokers --help
  ```

## Evaluation Procedure

The lab assignments will be assessed during the tutorials on the 25th of
September. 

During the assessment, you will start your consumer, and then start the 3
`experiment-producer`s. I will then verify whether you are succesfully
deserializing the messages. I might also request to have a look at how your are
deploying the producers and consumers.

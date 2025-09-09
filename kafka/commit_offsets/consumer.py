import signal
import random
import click 

from confluent_kafka import Consumer


def signal_handler(sig, frame):
    print('EXITING SAFELY!')
    exit(0)

signal.signal(signal.SIGTERM, signal_handler)


@click.command()
@click.argument('topic')
@click.argument('offset_reset')
def consume(topic: str, offset_reset: str): 
    c = Consumer({
        'bootstrap.servers': 'kafka1.dlandau.nl:19092,kafka2.dlandau.nl:29092,kafka3.dlandau.nl:39092',
        'group.id': f"{random.random()}",
        'auto.offset.reset': offset_reset,
        'security.protocol': 'SSL',
        'ssl.ca.location': './auth/ca.crt',
        'ssl.keystore.location': './auth/kafka.keystore.pkcs12',
        'ssl.keystore.password': 'cc2023',
        'enable.auto.commit': 'true',
        'ssl.endpoint.identification.algorithm': 'none',
    })

    c.subscribe(
        [topic], 
        on_assign=lambda _, p_list: print(p_list)
    )

    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("Consumer error: {}".format(msg.error()))
            continue
        print(msg.value())

consume()

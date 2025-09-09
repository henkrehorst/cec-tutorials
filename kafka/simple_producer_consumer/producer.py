import click

from confluent_kafka import Producer

p = Producer({
    'bootstrap.servers': 'kafka1.dlandau.nl:19092,kafka2.dlandau.nl:29092,kafka3.dlandau.nl:39092',
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

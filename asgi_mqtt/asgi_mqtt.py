
from argparse import ArgumentParser
from importlib import import_module
from signal import signal, SIGTERM, SIGINT
from time import sleep
import sys, logging
import paho.mqtt.client as mqtt

logger=logging.getLogger(__name__)

class AsgiMqtt(object):
    def __init__(self, channel, host, port, username, password):
        self._stop=False
        self._channel=self.getChannel(channel)
        self._host=host
        self._port=port
        self._username=username
        self._password=password

        self._client=mqtt.Client(
            userdata=dict(
                server=self,
                channel=self._channel,
                host=self._host,
                port=self._port
            )
        )
        self._client.on_connect=self.onConnect
        self._client.on_message=self.onMessage

    def getChannel(self, channelName):
        sys.path.insert(0,".")
        modulePath, objPath=channelName.split(":",1)
        channelLayer=import_module(modulePath)
        for part in objPath.split("."):
            channelLayer=getattr(channelLayer,part)
        return channelLayer

    @staticmethod
    def onConnect(client, userdata, flags, rc):
        logger.info("Connected with status: {}".format(rc))
        client.subscribe("#")

    @staticmethod
    def onMessage(client, userdata, message):
        logger.debug("Received message from topic: {}".format(message.topic))
        channel=userdata['channel']
        try: 
            channel.send(
                "mqtt.sub",
                dict(
                    topic=message.topic,
                    payload=message.payload,
                    qos=message.qos,
                    host=userdata['host'],
                    port=userdata['port'],
                    reply_channel="mqtt.pub",
                )
            )
        except Exception as e:
            logger.error("Cannot send message to channels!")
            logger.exception(e)

    def stop(self, sigNum, frame):
        logger.info("Received signal ({}), stopping".format(sigNum))
        self._stop=True

    def setupSignalHandlers(self):
        signal(SIGTERM, self.stop)
        signal(SIGINT, self.stop)

    def run(self):
        self.setupSignalHandlers()
        if self._username:
            self._client.username_pw_set(
                username=self._username,
                password=self._password
            )
        self._client.connect(self._host, self._port)
        logger.info("Starting MQTT loop")
        self._client.loop_start()
        while not self._stop:
            channel,msg=self._channel.receive(['mqtt.pub'],True)
            if channel and msg:
                self._client.publish(msg['topic'], msg['payload'])

        self._client.disconnect()

def main():
    parser=ArgumentParser(description="MQTT interface for Django/channels/ASGI")
    parser.add_argument("-H", "--host", help="MQTT Broker Host", default="localhost")
    parser.add_argument("-p", "--port", help="MQTT Broker Port", type=int, default=1883)
    parser.add_argument("-v", "--verbosity", help="Verbosity", action="count", default=0)
    parser.add_argument("channel_layer", help="ASGI Channel 'path.to.module:instance.path'")
    parser.add_argument("-u", "--username", help="MQTT Broker Username")
    parser.add_argument("-P", "--password", help="MQTT Broker Password")
    args=parser.parse_args()

    logging.basicConfig(
        level={0: logging.WARN, 1: logging.INFO}.get(args.verbosity, logging.DEBUG),
        format="%(asctime)-15s %(levelname)-8s %(message)s"
    )

    logger.info(
        "Starting ASGI({}) -> MQTT({}:{})".format(
            args.channel_layer, args.host, args.port
        )
    )

    AsgiMqtt(args.channel_layer, args.host, args.port, args.username, args.password).run()

if __name__=="__main__":
    main()

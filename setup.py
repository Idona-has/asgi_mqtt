import os.path as osp
import re
from setuptools import setup

def getVersion(package):
	init=open(osp.join(package, '__init__.py')).read()
	return re.search("^__version__=['\"]([^'\"]+)['\"]", init).group(1)

setup(
	name="asgi_mqtt",
	version=getVersion("asgi_mqtt"),
	author_email="info@idona.co.uk",
	url="https://github.com/Idona-has/asgi_mqtt",
	description="MQTT interface for Django/channels/ASGI",
	license="MIT",
	packages=["asgi_mqtt"],
	install_requires=["paho-mqtt"],
	entry_points=dict(console_scripts=["asgi_mqtt=asgi_mqtt.asgi_mqtt:main"])
)
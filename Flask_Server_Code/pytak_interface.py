#!/usr/bin/env python3

import asyncio
import xml.etree.ElementTree as ET
import pytak
from os import popen, environ
from sys import argv
from dotenv import load_dotenv
from configparser import ConfigParser
try:
    from icecream import ic as print
except:
    pass

LOCALHOST_IP = popen("hostname -I | cut -d' ' -f1").read().strip()
LONGITUDE = -97.52981
LATITUDE = 41.57625
MARKER_NAME = "Marker_1"
load_dotenv()

def gen_cot(index:int):
    """Generate CoT Event."""
    root = ET.Element("event")
    root.set("version", "2.0")
    root.set("type", "a-h-G-U-C-I")  # Hostile Infantry MIL2525 Marker
    root.set("uid", MARKER_NAME)
    root.set("how", "h-e")           # Estimated How
    root.set("time", pytak.cot_time())
    root.set("start", pytak.cot_time())
    root.set(
        "stale", pytak.cot_time(75000)
    )  # time difference in seconds from 'start' when stale initiates

    pt_attr = {
        "lon": f'{LONGITUDE}',
        "lat": f'{LATITUDE}',  
        "hae": "10",
        "ce": "999999.0",
        "le": "999999.0",
    }

    ET.SubElement(root, "point", attrib=pt_attr)


    print(ET.tostring(root))
    return ET.tostring(root)


class MySender(pytak.QueueWorker):
    """
    Defines how you process or generate your Cursor-On-Target Events.
    From there it adds the COT Events to a queue for TX to a COT_URL.
    """

    async def handle_data(self, data):
        """Handle pre-CoT data, serialize to CoT Event, then puts on queue."""
        event = data
        await self.put_queue(event)

    async def run(self, number_of_iterations=1):
        """Run the loop for processing or generating pre-CoT data."""
        i = 0
        while i != number_of_iterations:
            # print(data)
            data = gen_cot(i)
            self._logger.info("Sending:\n%s\n", data.decode())
            await self.handle_data(data)
            await asyncio.sleep(1)
            i += 1

class MyReceiver(pytak.QueueWorker):
    """Defines how you will handle events from RX Queue."""

    async def handle_data(self, data):
        """Handle data from the receive queue."""
        # self._logger.info("Received:\n%s\n", data.decode())  # Commented out to reduce clutter in cli
        pass

    async def run(self):  # pylint: disable=arguments-differ
        """Read from the receive queue, put data onto handler."""
        while 1:
            data = (
                await self.queue.get()
            )  # this is how we get the received CoT from rx_queue
            # print(data)
            await self.handle_data(data)


def try_set_global_value(global_variable:str, arg_idx:int ):
    """ Takes a global variable name and attempts to set it to the passed in value. """
    try:
            globals()[global_variable] = str(argv[arg_idx])
    except:
            print(f"Unable to set {global_variable} to value in argument index {arg_idx}")


async def main(latitude:float=None, longitude:float=None, marker_name:str=None ):
    global  LONGITUDE, LATITUDE, MARKER_NAME
    
    """ Defaults to setting the latitude and longitude to any passed value into the main function.
        If no values are passed into the function, then checks any cli arguments. 
        If neither exist, then it uses the default values set at the top of the file.
     """
    if latitude != None:
        LATITUDE = latitude
    else:
        try_set_global_value("LATITUDE", 1)

    if longitude != None:
        LONGITUDE = longitude
    else:
        try_set_global_value("LONGITUDE", 2)

    if marker_name != None:
        MARKER_NAME = marker_name
    else:
        try_set_global_value("MARKER_NAME", 3)    
    
    """Main definition of your program, sets config params and
    adds your serializer to the asyncio task list.
    """
    # print(LOCALHOST_IP, LONGITUDE, LATITUDE, MARKER_NAME)   # Debugging

    config = ConfigParser()
    config["mycottool"] = {
        "COT_URL": f"tls://{LOCALHOST_IP}:8089",
        "PYTAK_TLS_CLIENT_CERT": "admin.p12",
        "PYTAK_TLS_CLIENT_PASSWORD": os.getenv("PYTAK_TLS_CLIENT_PASSWORD"),
        "PYTAK_TLS_DONT_VERIFY":1,
        "DEBUG": 0,
        }
    config = config["mycottool"]

    # Initializes worker queues and tasks.
    clitool = pytak.CLITool(config)
    await clitool.setup()

    # Add your serializer to the asyncio task list.
    clitool.add_tasks(
        set([MySender(clitool.tx_queue, config), MyReceiver(clitool.rx_queue, config)])
    )

    # Start all tasks.
    await clitool.run()


if __name__ == "__main__":
    asyncio.run(main())
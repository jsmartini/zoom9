from serial import Serial
import pickle
import timeit
import datetime
import pandas
import logging
from enum import Enum

global device

class PacketStatus(Enum):
    ACK = "ACK"
    CON = "CON"
    FIN = "FIN"

def pack(data, status:PacketStatus):
    pickled = pickle.dumps(data)
    return bytearray(f"ZZZ{str(status)}BBB{len(pickled)}C".encode()) + pickled

def unpack(packet):
    """
    test suite for unpacking algorithm
    :param packet:
    :return:
    """
    flags = {"Z":0, "B":0}
    meta = {"status":"", "length": ""}
    def reset():
        for i in flags.keys(): flags[i] = 0
        for i in meta.keys(): meta[i] = ""
    for cnt, i in enumerate(packet):
        # cycles through all Z's until status
        if chr(i) == "Z" and flags["Z"] < 3:
            flags["Z"] += 1
            continue
        # puts everything between Z & B into status string
        if flags["Z"] == 3 and chr(i) != "B" and len(meta["status"]) < 3:
            meta["status"] += chr(i)
            continue
        #cycles through B's until length
        if chr(i) == "B" and flags["B"] < 3:
            flags["B"] += 1
            continue
        if flags["B"] == 3 and chr(i) != "C":
            meta["length"] += chr(i)
            continue
        if flags["B"] == 3 and chr(i) == "C":
            #return tuple (py object, status)
            #cnt + 1 because we are at C not the first datum of serialized pickle
            return (pickle.loads(packet[cnt+1:cnt+1+int(meta["length"])]), meta["status"])

import asyncio

from uuid import uuid4
from time import sleep
import time

class z9c(Serial):
    def __init__(self, dev, baud=115200):
        super().__init__(port=dev, baudrate=baud)
        logging.info(f"Initialized Device {dev} @Baudrate {baud}")
        self.connection = False
        self.try_timeout = 50
        self.id = str(uuid4())
        logging.info(f"Created Serial Device for resource {dev} as ID:{self.id}")
        self.establish_connection()

    def establish_connection(self):
        pkt=self.id
        while not self.connection and self.try_timeout >= 0:
            self.send(pkt, status="ACK")
            if (r := self.recv())[1] == "ACK":
                self.connection = True
                logging.info(f"Successfully connected to ID: {r[0]}\tpacket status {r[1]}")
                return
            else:
                self.try_timeout -= 1
                print(f"Try: {self.try_timeout} \tWaiting to receive ACK connection packet: waiting . . . \r")
                sleep(0.5)

        raise("Connection failed")
        exit(-1)

    def send(self, data, status="CON"):
        """
        sends data to serial port
        :param data: python object
        :param status: connection status
        :return: bytes written
        """
        return super().write(pack(data, status=status))

    def recv(self):
        """
        python coroutine to listen, parse packets, and move python messages to objBuffer stack

        slow algorithm

        originally made for asyncio; pyserial doesn't support asyncio; lots of unnecessary code
        :return:
        """
        flags = {"Z": 0, "B": 0}
        meta = {"status": "", "length": ""}
        def reset():
            """
            resets if data corruption detected via mis-matches
            :return: None
            """
            for i in flags.keys(): flags[i] = 0
            for i in meta.keys(): meta[i] = ""
            return (None, "CON")
        while True:
            if not super().inWaiting() > 0: return (None, "CON")
            i = super().read(1)
            if chr(i) == "Z" and flags["Z"] < 3:
                flags["Z"] += 1
                continue
            elif flags["Z"] < 3 and chr(i) != "Z": reset()  #corruption condition
            # puts everything between Z & B into status string
            if flags["Z"] == 3 and chr(i) != "B" and len(meta["status"]) < 3:
                meta["status"] += chr(i)
                continue
            # cycles through B's until length
            if chr(i) == "B" and flags["B"] < 3:
                flags["B"] += 1
                continue
            elif flags["B"] < 3 and chr(i) != "B": reset() #corruption condition
            if flags["B"] == 3 and chr(i) != "C":
                meta["length"] += chr(i)
                continue
            if flags["B"] == 3 and chr(i) == "C":
                # return tuple (py object, status)
                super().read(1) #kick "C" out of the serial buffer
                return (
                    pickle.loads(super().read(meta["length"])),
                    meta["status"]
                )

from os import system

def term(dev, baud):
    """
    opens telnet client for configuring radio hardware settings
    :param dev:
    :param baud:
    :return:  none
    """
    system(f"python3 -m serial.tools.miniterm {dev} {baud}")
    print(f"Reload {dev} - bug when in miniterm causes connection to stay open past process")
    exit(0)

from textwrap import dedent
def ping_pong(dev, baud):
    device = z9c(dev, baud)
    while 1:
        msg = input("?>")
        if msg.upper() == "help":
            print(dedent(
                """
                Ping Pong z9c help menu:
                ===========================
                help -      help menu
                exit -      exit
                """
            ))
        device.send(msg)
        print(device.send(msg))

if __name__ == "__main__":
    """
    Test Code
    """
    msg = dedent(
        """
            /$$$$$$                    /$$                         /$$
           /$$__  $$                  | $$                        | $$
 /$$$$$$$$| $$  \ $$  /$$$$$$$       /$$$$$$    /$$$$$$   /$$$$$$ | $$
|____ /$$/|  $$$$$$$ /$$_____/      |_  $$_/   /$$__  $$ /$$__  $$| $$
   /$$$$/  \____  $$| $$              | $$    | $$  \ $$| $$  \ $$| $$
  /$$__/   /$$  \ $$| $$              | $$ /$$| $$  | $$| $$  | $$| $$
 /$$$$$$$$|  $$$$$$/|  $$$$$$$        |  $$$$/|  $$$$$$/|  $$$$$$/| $$
|________/ \______/  \_______/         \___/   \______/  \______/ |__/
        
        Jonathan Martini @2021 Alabama Rocketry Association
        """
    )
    msg2 = dedent("""
    
    
 ________    ______      ______   ___      ___   _______    
("      "\  /    " \    /    " \ |"  \    /"  | /" _   "\   
 \___/   :)// ____  \  // ____  \ \   \  //   |(: (_/  :|   
   /  ___//  /    ) :)/  /    ) :)/\\  \/.    | \____/ |)   
  //  \__(: (____/ //(: (____/ //|: \.        |    _\  '|   
 (:   / "\\        /  \        / |.  \    /:  |   /" \__|\  
  \_______)\"_____/    \"_____/  |___|\__/|___|  (________) 
                                                            

    Jonathan Martini @2021 Alabama Rocketry Association
    
    
    """)
    print(msg2)
    import argparse
    parser = argparse.ArgumentParser(
        description= "z9c software test suite and debug tools",
        prog="z9c test suite"
    )
    parser.add_argument("Port", metavar="P", type=str, help="Serial Device Port")
    parser.add_argument('Baud', metavar="B", type=int, help="Serial Device Baudrate")
    parser.add_argument("-T", "--Terminal", action="store_true", help="Serial Device Telnet Terminal")
    args = parser.parse_args()
    if args.Terminal:
        term(args.Port, args.Baud)
    else:
        ping_pong(args.Port, args.Baud)




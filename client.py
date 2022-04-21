"""Small example OSC server
This program listens to several addresses, and prints some information about
received packets.
"""
import argparse
from pythonosc import dispatcher
from pythonosc import osc_server
import pandas as pd

class OSCData():
    data = []
    feat = []
    def handle_data(self, *args):
        self.data.append(args)
        print(args)
    def handle_feat(self, *args):
        self.feat.append(args)
        print(args)

# def print_volume_handler(unused_addr, args, volume):
#     print("[{0}] ~ {1}".format(args[0], volume))

# def print_compute_handler(unused_addr, args, volume):
#     try:
#         print("[{0}] ~ {1}".format(args[0], args[1](volume)))
#     except ValueError: pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", default="127.0.0.1", help="The ip to listen on")
    parser.add_argument("--port", type=int, default=8889, help="The port to listen on")
    args = parser.parse_args()

    SD = OSCData()
    dispatcher = dispatcher.Dispatcher()
    dispatcher.map("/data", SD.handle_data)
    dispatcher.map("/feat", SD.handle_feat)

    # dispatcher.map("/volume", print_volume_handler, "Volume")
    # dispatcher.map("/logvolume", print_compute_handler, "Log volume", math.log)

    server = osc_server.ThreadingOSCUDPServer(
      (args.ip, args.port), dispatcher)
    print("Serving on {}".format(server.server_address))

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pd.DataFrame(SD.data).to_csv("data.csv")
        pd.DataFrame(SD.feat).to_csv("feat.csv")
        print("k")


import argparse


class Configurator:
    """static configurator class"""
    @staticmethod
    def get_user_config():
        parser = argparse.ArgumentParser(description='Environment simulator for the Hurricane Evacuation Problem')
        # part I
        parser.add_argument('-g', '--graph',         default='./config/graph.config',   help='path to graph initial configuration file')
        parser.add_argument('-V', '--v_no_ops',      default='1',   type=int,           help='number of vandal agent\'s no-ops before taking action')
        parser.add_argument('-K', '--base_penalty',  default='2',   type=int,           help='base penalty for losing an evacuation vehicle')
        parser.add_argument('-d', '--debug',         default=True,  action='store_true',help='run in debug mode')
        args = vars(parser.parse_args())
        for k, v in args.items():
            setattr(Configurator, k, v)
        print("Environment Configurated.")
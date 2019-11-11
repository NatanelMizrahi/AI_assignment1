import argparse


class Configurator:
    """static configurator class"""
    @staticmethod
    def get_user_config():
        parser = argparse.ArgumentParser(description='Environment simulator for the Hurricane Evacuation Problem')
        # part I
        parser.add_argument('-g', '--graph',         default='./config/graph.config', help='path to graph initial configuration file')
        parser.add_argument('-V', '--v_no_ops',      default='1', type=int,           help='number of vandal agent\'s no-ops before taking action')
        parser.add_argument('-K', '--base_penalty',  default='2', type=int,           help='base penalty for losing an evacuation vehicle')
        args = vars(parser.parse_args())
        for k, v in args.items():
            setattr(Configurator, k, v)
        print("Environment Configurated.")


# class Configurator:
#     """Singleton configurator class"""
#     inst = None
#
#     @staticmethod
#     def get_instance():
#         """ Static access method. """
#         if Configurator.inst is None:
#             Configurator()
#         return Configurator.inst
#
#     def __init__(self):
#         """ Virtually private constructor. """
#         if Configurator.inst is None:
#             Configurator.inst = self
#             self.config = self.get_user_config()
#         else:
#             raise Exception("Configurator is a singleton!")
#
#     def get_user_config(self):
#         parser = argparse.ArgumentParser(description='''
#             **Environment simulator for the Hurricane Evacuation Problem**
#             Provide the parameters for the simulator.
#         ''')
#         # part I
#         parser.add_argument('-g', '--graph',    default='./config/graph.config',    help='path to graph initial configuration file')
#         parser.add_argument('-K', '--penalty',  default='2',    type=int,           help='base penalty for losing an evacuation vehicle')
#         parser.add_argument('-V', '--v_no_ops', default='1',    type=int,           help='number of vandal agent\'s no-ops before taking action')
#         return parser.parse_args()
#
#     def get_noops(self):
#         return self.config.v_no_ops

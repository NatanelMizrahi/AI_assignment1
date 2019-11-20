from enum import Enum


class ActionType(Enum):
    NO_OP     = 0
    GOTO      = 1
    BLOCK     = 2
    TERMINATE = 3


class Action:
    """Data structure for describing an agent's action"""
    def __init__(self,
                 agent,
                 # optional arguments
                 action_type: ActionType=None,
                 description='',
                 end_time=0,
                 callback=None):
        self.agent = agent
        self.action_type = action_type
        self.description = description
        self.end_time = end_time
        self.callback = callback

    def execute(self):
        if self.callback is not None:
            self.callback()
            print('[DONE]' + self.description)

    def describe(self):
        print(self.description)

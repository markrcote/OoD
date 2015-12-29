import sys

from ood.controllers.simple import SimpleServerController
from ood.state import State, StateMachine as StateMachineBase


class Archived(State):
    name = 'archived'


class Starting(State):
    name = 'starting'
    timeout = 10

    def on_timeout(self):
        if self.machine.controller.mcc.port_open():
            self.machine.go_to_state('running')
            return True
        return False


class Running(State):
    name = 'running'
    timeout = 60

    def on_timeout(self):
        self.machine.controller.mcc.check_for_players()
        if self.machine.controller.mcc.timeout_no_players():
            self.machine.controller.stop()
            self.machine.go_to_state('stopping')
            return True
        return False


class Stopping(State):
    name = 'stopping'
    timeout = 10

    def on_timeout(self):
        if not self.machine.controller.running():
            self.machine.go_to_state('archived')
            return True
        return False


class StateMachine(StateMachineBase):
    module = sys.modules[__name__]
    controller_class = SimpleServerController
    unknown_state_name = 'archived'
    start_state_name = 'starting'
    stop_state_name = 'stopping'

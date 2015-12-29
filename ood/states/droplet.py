import logging
import sys

from ood.controllers.droplet import DropletController
from ood.state import State, StateMachine as StateMachineBase


class Unknown(State):
    name = 'unknown'


class DropletState(State):
    def on_timeout(self):
        archived = (self.machine.controller.droplet is None or
                    self.droplet_status == 'archive')

        if archived:
            self.machine.go_to_state('archived')
            return True

        return False

    @property
    def droplet_status(self):
        if self.machine.controller.droplet is None:
            return None

        return self.machine.controller.droplet.status


class Archived(DropletState):
    name = 'archived'


class Restoring(DropletState):
    name = 'restoring'
    timeout = 30

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        if self.droplet_status == 'active':
            self.machine.go_to_state('starting')
            return True

        return False


class Starting(DropletState):
    name = 'starting'
    timeout = 10

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        if self.machine.controller.running():
            self.machine.controller.mcc.reset_player_info()
            self.machine.go_to_state('running')
            return True

        return False


class Running(DropletState):
    name = 'running'
    timeout = 60

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        # This is duplicated in the SimplerServer Running state.
        self.machine.controller.mcc.check_for_players()
        if self.machine.controller.mcc.timeout_no_players():
            self.machine.controller.stop()
            self.machine.go_to_state('stopping')
            return True

        return False


class Stopping(DropletState):
    name = 'stopping'
    timeout = 10

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        if not self.machine.controller.running():
            self.machine.controller.shutdown()
            self.machine.go_to_state('shutting down')
            return True

        return False


class ShuttingDown(DropletState):
    name = 'shutting down'
    timeout = 20

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        if self.droplet_status == 'off':
            self.machine.controller.snapshot()
            self.machine.go_to_state('snapshotting')
            return True

        return False


class Snapshotting(DropletState):
    name = 'snapshotting'
    timeout = 30

    def on_timeout(self):
        if DropletState.on_timeout(self):
            return True

        if self.machine.controller.snapshot_action is None:
            logging.error('No snapshot action while in SNAPSHOTTING '
                          'state!')
            self.machine.go_to_state('unknown')
            # TODO: we could try to find an in-progress snapshot action
            # associated with our droplet, if we have one.
            return

        if self.machine.controller.snapshot_action.status == 'completed':
            logging.info('Snapshot completed: %s %s.' %
                         (self.machine.controller.snapshot_action.resource_type,
                          self.machine.controller.snapshot_action.resource_id))
            self.machine.controller.clear_snapshot_action()
            self.machine.controller.destroy()
            self.machine.go_to_state('destroying')
        elif self.machine.controller.snapshot_action.status == 'errored':
            logging.error('Error taking snapshot!')
            self.machine.go_to_state('unknown')

    @property
    def snapshot_action(self):
        return None


class Destroying(DropletState):
    name = 'destroying'
    timeout = 10

    # Uses default on_timeout().


class StateMachine(StateMachineBase):
    module = sys.modules[__name__]
    controller_class = DropletController
    unknown_state_name = 'unknown'
    start_state_name = 'restoring'
    stop_state_name = 'stopping'

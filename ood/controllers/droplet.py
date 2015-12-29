import logging
import os
import time
from operator import attrgetter

import digitalocean
from paramiko.client import AutoAddPolicy, SSHClient

from ood.minecraft import Client
from ood.models import DropletState

# TODO: Make all this configurable.
DROPLET_NAME = 'ood'
REGION = 'nyc3'
MINECRAFT_PORT = 25898
MINECRAFT_RCON_PORT = 25899

# TODO: This should be in the database and configurable.
DEFAULT_DATA_DIR = os.path.join(os.getenv('HOME'), '.ood')
DROPLET_KEY_FILENAME = 'droplet_key'
DROPLET_ROOT_SSH_KEY_FILENAME = 'ssh_key'
RCON_PW_FILENAME = 'rcon_pw'


class DropletController(object):

    def __init__(self, ood_instance, data_dir=DEFAULT_DATA_DIR):
        self.state, _ = DropletState.objects.get_or_create(ood=ood_instance)
        self.mcc = Client(ood_instance)
        self.data_dir = os.path.expanduser(data_dir)
        if not os.path.exists(self.data_dir):
            os.mkdir(self.data_dir)

        self.api_key_path = os.path.join(self.data_dir, DROPLET_KEY_FILENAME)
        self.ssh_key_path = os.path.join(self.data_dir,
                                         DROPLET_ROOT_SSH_KEY_FILENAME)
        self.rcon_pw_path = os.path.join(self.data_dir, RCON_PW_FILENAME)

        self._snapshot_action = None
        self._droplet_ip = None
        self._refresh_droplet()

    def start(self):
        """Starts up a droplet from the most recent snapshot."""
        snapshot = self._find_snapshot()
        if snapshot is None:
            logging.error('No ood snapshot found.')
            return

        ssh_key = self._find_ssh_key()
        if ssh_key is None:
            logging.error('No ood ssh key found.')
            return

        self.droplet = digitalocean.Droplet(token=self.api_key,
                                            name='ood',
                                            region=REGION,
                                            image=snapshot.id,
                                            size_slug='1gb',
                                            ssh_keys=[ssh_key])
        self.droplet.create()

    def stop(self):
        """Starts the stop-snapshot-destroy process."""
        self._refresh_droplet()
        logging.info('Stopping Minecraft.')
        self._exec_ssh_cmd('supervisorctl stop minecraft')

    def shutdown(self):
        logging.info('Shutting down host.')
        self.droplet.shutdown()
        # TODO: Keep the action object and use it to verify state (but
        # double check that the state is 'off' after).
        # TODO: Call self.droplet.poweroff() if shutdown() fails or takes
        # too long.

    def snapshot(self, shutdown_error=None):
        if self.droplet is None:
            logging.error('Cannot start snapshot: no droplet.')
            return

        if self.snapshot_action:
            logging.error('Cannot start snapshot: snapshot in progress.')
            return

        snapshot_name = '%s-%d' % (DROPLET_NAME, time.time())
        if shutdown_error:
            snapshot_name += '-error'

        self.state.snapshot_action_id = self.droplet.take_snapshot(
            snapshot_name)['action']['id']
        self.state.save()

    def destroy(self):
        self.droplet.destroy()

    def clear_snapshot_action(self):
        self.state.snapshot_action_id = None
        self.state.save()

    def running(self):
        return self.mcc.port_open()

    @property
    def api_key(self):
        return file(self.api_key_path).read().strip()

    @property
    def droplet_ip(self):
        if self._droplet_ip:
            return self._droplet_ip

        # TODO: Should maybe refresh droplet here.  Dependencies are unclear.
        if self.droplet is None:
            return None

        for network in self.droplet.networks['v4']:
            if network['type'] == 'public':
                self._droplet_ip = network['ip_address']
                return self._droplet_ip

        return None

    @property
    def manager(self):
        return digitalocean.Manager(token=self.api_key)

    @property
    def snapshot_action(self):
        if self.state.snapshot_action_id is None:
            return None
        if (self._snapshot_action is None or
            self._snapshot_action.id != self.state.snapshot_action_id):
            # TODO: The action might not exist anymore, in which case we need
            # to clear the id variable.
            self._snapshot_action = digitalocean.Action.get_object(
                self.api_key, self.state.snapshot_action_id)
        return self._snapshot_action

    def _find_ssh_key(self):
        for key in self.manager.get_all_sshkeys():
            if key.name == 'ood':
                return key
        return None

    def _find_snapshot(self):
        snapshots = sorted([img for img in self.manager.get_my_images()
                            if img.name.startswith('%s-' % DROPLET_NAME)],
                           key=attrgetter('name'), reverse=True)

        if not snapshots:
            return None

        return snapshots[0]

    def _refresh_droplet(self):
        for droplet in self.manager.get_all_droplets():
            if droplet.name == DROPLET_NAME:
                self.droplet = droplet
                if self.state.droplet_ip_address != self.droplet_ip:
                    self.state.droplet_ip_address = self.droplet_ip
                    self.state.save()
                    self.mcc.update_host(
                        self.state.droplet_ip_address,
                        MINECRAFT_PORT,
                        MINECRAFT_RCON_PORT,
                        file(self.rcon_pw_path).read().strip()
                    )
                break
        else:
            self.droplet = None

    def _exec_ssh_cmd(self, cmdline):
        client = SSHClient()
        client.set_missing_host_key_policy(AutoAddPolicy())
        client.connect(self.droplet_ip, username='root',
                       key_filename=self.ssh_key_path)
        stdin, stdout, stderr = client.exec_command(cmdline)
        for line in stdout:
            logging.info(line)
        for line in stderr:
            logging.info(line)

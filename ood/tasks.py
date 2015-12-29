from __future__ import absolute_import

import logging

from ood.celery import app
from ood.models import OodInstance
from ood.states.droplet import StateMachine as DropletStateMachine
from ood.states.simple import StateMachine as SimpleStateMachine


def get_state_machine(ood_instance):
    sm = None
    if ood_instance.server_type == OodInstance.SIMPLE_SERVER:
        sm = SimpleStateMachine(ood_instance)
    elif ood_instance.server_type == OodInstance.DROPLET_SERVER:
        sm = DropletStateMachine(ood_instance)
    return sm


@app.task
def update_state():
    instances = OodInstance.objects.all()
    for instance in instances:
        get_state_machine(instance).update()


@app.task
def start(instance_id):
    logging.info('Request to start instance %d.' % instance_id)
    instance = OodInstance.objects.get(pk=instance_id)
    sm = get_state_machine(instance)
    if not sm.controller.running():
        sm.controller.start()
        sm.go_to_state(sm.start_state_name)


@app.task
def stop(instance_id):
    logging.info('Request to stop instance %d.' % instance_id)
    instance = OodInstance.objects.get(pk=instance_id)
    sm = get_state_machine(instance)
    if sm.controller.running():
        sm.controller.stop()
        sm.go_to_state(sm.stop_state_name)

#!/usr/bin/python3

# use ansible to determine connection and copy over a file

import os
import json
import yaml
#import shutil
import socket
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager
from ansible.inventory.manager import InventoryManager
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible import context
import ansible.constants as C

pwd = os.getcwd()

class ResultCallback(CallbackBase):
    def v2_runner_on_ok(self, result, **kwargs):
        host = result._host
        print(json.dumps({host.name: result._result}, indent=4))

context.CLIARGS = ImmutableDict(connection='local', module_path=['/usr/lib/python3/dist-packages/ansible'], forks=10, become=None,
                                become_method=None, become_user=None, check=False, diff=False)

def playbook(host_play):
    loader = DataLoader()

    inventory = InventoryManager(loader=loader, sources=pwd + '/hosts')

    variable_manager = VariableManager(loader=loader, inventory=inventory)

    passwords = dict(vault_pass='false')

    play_source = dict(
        name = "ansible play",
        hosts = str(host_play),
        gather_facts = 'no',
        tasks = [
            dict(action=dict(module='ping'), register='ping_out'),
            dict(action=dict(module='debug', args=dict(msg='{{ping_out.stdout}}')))
        ]
    )

    play = Play().load(play_source, variable_manager=variable_manager, loader=loader)

    tqm = None
    try:
        tqm = TaskQueueManager(
                inventory=inventory,
                variable_manager=variable_manager,
                loader=loader,
                passwords=passwords,
                stdout_callback=results_callback
            )
        result = tqm.run(play)
    finally:
        if tqm is not None:
            tqm.cleanup()
    return(result)

def check_port(host, port):
    socket_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(host)
    host_ip = socket.gethostbyname(host)
    ssh_test = (str(host_ip), port)
    if (socket_check.connect_ex(ssh_test) == 0):
        print("good connection on " + str(port) + ": " + host_ip)
        socket_check.close()
        return(True)
    else:
        print("no connection on " + str(port) + ": " + host_ip)
        socket_check.close()
        return(False)

linux_list = []
win_list = []

results_callback = ResultCallback()

with open(pwd + '/vars.yaml', 'r') as v:
    input_hosts = yaml.safe_load(v)

for k,v in input_hosts.items():
    for i in v:
        if (check_port(i, 22)):
            linux_list.append(i)

for k,v in input_hosts.items():
    for i in v:
        if (check_port(i, 5985)):
            win_list.append(i)

if (len(linux_list) > 0):
    print("Linux hosts:\n")
    for host in linux_list:
        linux_stdout = playbook(host)
        print(linux_stdout)
if (len(win_list) > 0):
    print("Windows hosts:\n")
    for host in win_list:
        win_stdout = playbook(host)
        print(win_stdout)

exit
#!/usr/bin/env python3
# This code is based on:
# https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/compute/api/create_instance.py
import time

def list_instance_names(compute, project, zone):
    result = compute.instances().list(project=project, zone=zone).execute()
    names = []
    for r in result['items']:
        names.append(r['name'])
    return names

def wait_for_operation(compute, project, zone, operation):
    print('Waiting for operation to finish...')
    while True:
        result = compute.zoneOperations().get(
            project=project,
            zone=zone,
            operation=operation).execute()

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                raise Exception(result['error'])
            return result
        
        time.sleep(1)

def delete_instance(compute, project, zone, name):
    request = compute.instances().delete(project=project, zone=zone, name=name)
    return request.execute()


def create_boot_disk_from_snapshot(compute, project, zone, disk_name, snapshot_name):
    snapshot_url = 'projects/{}/global/snapshots/{}'.format(project, snapshot_name)
    request = compute.disks().insert(project=project,
                                     zone=zone,
                                     body={'name': disk_name, 'sourceSnapshot': snapshot_url})
    return request.execute()


def create_instance_from_boot_disk(compute, project, zone, instance_name, boot_disk_name):
    machine_type = "zones/{}/machineTypes/n1-standard-1".format(zone)
    source = "projects/{}/zones/{}/disks/{}".format(project, zone, boot_disk_name)
    network = "projects/{}/global/networks/default".format(project)
    config = {
        'name': instance_name,
        'machineType': machine_type,
        'disks': [
            {
                'boot': True,
                'mode': 'READ_WRITE',
                'deviceName': boot_disk_name,
                'autoDelete': False,
                'source': source
            }
        ],
        "networkInterfaces": [
            {
                "network": network,
                "accessConfigs": [
                    {
                        "name": "External NAT",
                        "type": "ONE_TO_ONE_NAT"
                    }
                ]
            }
        ],
    }

    request = compute.instances().insert(project=project,
                                         zone=zone,
                                         body=config)
    return request.execute()


def create_cluster(compute, project, zone, cluster_name, num_instances, snapshot_name):
    for i in range(num_instances):
        instance_name = cluster_name + "-" + str(i)
        boot_disk_name = instance_name
        operation = create_boot_disk_from_snapshot(compute, project, zone, boot_disk_name, snapshot_name)
        wait_for_operation(compute, project, zone, operation['name'])
        create_instance_from_boot_disk(compute, project, zone, instance_name, boot_disk_name)

    return

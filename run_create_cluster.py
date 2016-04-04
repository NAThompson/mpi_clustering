#!/usr/bin/env python3.5

import time
import argparse
import subprocess
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from create_cluster import create_cluster, list_instance_names, delete_instance


def main(project, zone, cluster_name, num_instances, snapshot_name):
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    print('Creating cluster . . .')

    new_instances = create_cluster(compute, project, zone, cluster_name, num_instances, snapshot_name)
    
    print("new instances: {}".format(new_instances))

    print("Running mpi job:")
    cmd = "mpirun -np {} --host ".format(len(new_instances))
    for instance in new_instances:
        cmd += "{},".format(instance)

    cmd += " mpi_hello.x"
    print("Command about to be run:\n {}".format(cmd))

    # gcloud recycles the internal IP address alot, leading to MITM warnings:
    subprocess.run('echo "" > ~/.ssh/known_hosts', shell=True, check=True)
    # Give the cluster some time to warm up, otherwise we'll get "Connection Refused"
    time.sleep(15)
    subprocess.run(cmd, shell=True, check=True)
    print("Computation done, deleting instances:")
    for instance in new_instances:
        delete_instance(compute, project, zone, instance)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('project_id',
                        help='Your Google Cloud project ID.')

    parser.add_argument('--zone', default='us-central1-c',
                        help='Compute Engine zone to deploy to.')

    parser.add_argument('--cluster_name', default='demo-cluster',
                        help='New instance name.')

    parser.add_argument('--nodes', default=5, type=int,
                        help='Number of nodes in cluster')

    parser.add_argument('--snapshot_name', default='mpi-snapshot',
                        help='Name of snapshot')

    args = parser.parse_args()

    main(args.project_id, args.zone, args.cluster_name, args.nodes, args.snapshot_name)

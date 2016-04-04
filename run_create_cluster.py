#!/usr/bin/env python3

import argparse
from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from create_cluster import create_cluster, list_instance_names


def main(project, zone, cluster_name, num_instances, snapshot_name):
    credentials = GoogleCredentials.get_application_default()
    compute = discovery.build('compute', 'v1', credentials=credentials)

    print('Creating cluster . . .')

    create_cluster(compute, project, zone, cluster_name, num_instances, snapshot_name)

    instances = list_instance_names(compute, project, zone)
    print("We now have the following instances:")
    for instance in instances:
        print(instance)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('project_id',
                        help='Your Google Cloud project ID.')

    parser.add_argument('--zone', default='us-central1-c',
                        help='Compute Engine zone to deploy to.')

    parser.add_argument('--cluster_name', default='demo-cluster',
                        help='New instance name.')

    parser.add_argument('--nodes', default=5,
                        help='Number of nodes in cluster')

    parser.add_argument('--snapshot_name', default='mpi-node',
                        help='Name of snapshot')

    args = parser.parse_args()

    main(args.project_id, args.zone, args.cluster_name, args.nodes, args.snapshot_name)

Creating an MPI Cluster on gcloud
=================================

    A quick tutorial

-----------------------
Running a basic MPI job
-----------------------

This tutorial will assume Ubuntu 15.10, but any Debian system should be fine.

To begin, let's rent a machine from gcloud:

.. code:: bash

   $ gcloud compute instances create mpi-test --machine-type n1-standard-4 \
     --image ubuntu-15-10 --preemptible --scopes=compute-rw

A bit of explanation:

  - We make it preemptible so if we forget to turn it off, it'll be cheaper.
  - We give it the 'compute-rw' scope so that it has permission to ssh between nodes
  - We choose the 'n1-standard-4' machine type so we have 4 cores to practice parallelism

Let's go to this instance and install our tools:

.. code:: bash

   $ gcloud compute ssh mpi-test
   mpi-test$ sudo apt-get update && sudo apt-get install -y gcc libopenmpi-dev openmpi-bin

Now let's run a super-trivial example; call it mpi_hello.c

.. code:: c

    #include <stdio.h>
    #include <mpi/mpi.h>

    int main (int argc, char** argv)
    {
        int rank, size;

        MPI_Init (&argc, &argv);
        MPI_Comm_rank (MPI_COMM_WORLD, &rank); 
        MPI_Comm_size (MPI_COMM_WORLD, &size);
        printf( "Hello world from process %d of %d\n", rank, size );
        MPI_Finalize();
        return 0;
    }

Now we build and run via

.. code:: bash

    $ gcc -c mpi_hello.c
    $ gcc -o mpi_hello.x mpi_hello.o -lmpi
    $ mpirun -np $(nproc) mpi_hello.x
    Hello world from process 2 of 4
    Hello world from process 3 of 4
    Hello world from process 1 of 4
    Hello world from process 0 of 4

So it works.

----------------------------
Renting a group of instances
----------------------------

Now let's rent a group of instances on gcloud, ensuring that their state is identical using the following startup script (call it startup.sh):

.. code:: bash

    #!/bin/bash

    sudo apt-get update
    sudo apt-get install -y libopenmpi-dev openmpi-bin

We then issue the following command to obtain the nodes:

.. code:: bash

   $ gcloud compute instances create mpi-node-{1..5} --metadata-from-file startup-script=startup.sh \
     --image ubuntu-15-10 --machine-type n1-standard-4 --preemptible --scopes=compute-rw
   ERROR: (gcloud.compute.instances.create) Some requests did not succeed:
   	  - Quota 'CPUS' exceeded.  Limit: 8.0

Whoops! We need to increase our CPU quota limit before proceeding, we need to fill out a quota_ change request form.
Once this is done, we re-run the previous command to obtain our nodes.

--------------------------------------------
Making our group of instances into a cluster
--------------------------------------------

In order to run our job using our newly created nodes, we need to create a "hosts" file:

.. code:: bash

   $ for i in `seq 1 5`; do echo "mpi-node-$i" >> hosts.txt; done

Now we run with

.. code:: bash

   $ mpirun -np $(nproc) --hostfile mpi_hosts.txt mpi_hello.x

But this gives us a problem which thwart our goal of non-interactivity:

.. code:: bash

   $ mpirun -np $(nproc) --hostfile mpi_hosts.txt mpi_hello.x
   The authenticity of host 'mpi-node-4 (10.240.0.7)' can't be established.
   ECDSA key fingerprint is SHA256:u3+p4T8hr4VIqQianiIwatkTe2iiYWgdHM1VfLGG8ro.
   Are you sure you want to continue connecting (yes/no)? The authenticity of host 'mpi-node-2 (10.240.0.6)' can't be established.
   ECDSA key fingerprint is SHA256:l8mMQc9T9m0zvB1ZWqnaBnZ04kEbJ7+tYBUGOoCpXWI.
   Are you sure you want to continue connecting (yes/no)? The authenticity of host 'mpi-node-1 (10.240.0.9)' can't be established.
   ECDSA key fingerprint is SHA256:0VgW0A7vlbKr0JFfnbBB3AnyFft8eJ7KTRC68INZNuU.
   Are you sure you want to continue connecting (yes/no)? The authenticity of host 'mpi-node-3 (10.240.0.5)' can't be established.
   ECDSA key fingerprint is SHA256:W42YmeCOE+bwZqyLx8YvM1spcEBbEHreQkHK+DYTxZs.
   Are you sure you want to continue connecting (yes/no)?

This is a pain; here's an easy fix (with an obvious security implication):

.. code:: bash

   $ echo "StrictHostKeyChecking no" | sudo tee --append /etc/ssh/ssh_config

And then we get a different problem:

.. code:: bash

   $ mpirun -v -np $(nproc) --hostfile hosts.txt mpi_hello.x
   ssh: connect to host mpi-node-1 port 22: Connection timed out
   $ mpirun -np $(nproc) --hostfile hosts.txt mpi_hello.x
   Permission denied (publickey).
  
Unfortunately, we have to learn about SSH before continuing:

--------------------
A diversion into ssh
--------------------

Since MPI performs internode communication over ssh, the following basic operation must succeed before we can have any hope of running multinode MPI:

.. code:: bash

   local-host$ ssh remote-host
   
For ssh to work, the remote machine must authenticate the local, and the local must authenticate the remote.
We've already told our local machine to not worry about authenticating the remote via

.. code:: bash

   local-host$ echo "StrictHostKeyChecking no" | sudo tee --append /etc/ssh/ssh_config

This ensure that we will not be prompted about trusting the remote machine the first time we connect.
To make what is happening a bit more transparent, we run the following command:

.. code:: bash

   local-host$ echo "HashKnownHosts No" | sudo tee --append ~/.ssh/config

Then we attempt to connect to the remote via:

.. code:: bash

   local-host$ ssh remote-host
   Warning: Permanently added 'remote,10.240.0.9' (ECDSA) to the list of known hosts.
   Permission denied (publickey).
   local-host$ cat ~/.ssh/known_hosts
   remote-host,10.240.0.9 ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBL1HBgcYP+Q+S+jmcZEKnVgm5AZXWychzkB10nKMjYcYLeAfPkVJwTkrq5g+ILslzSEf5RlXRfOzHQBGBoiaYKY=

This is copied from the remote:

.. code:: bash

   remote-host$ sudo cat /etc/ssh/ssh_host_ecdsa_key.pub
   ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBL1HBgcYP+Q+S+jmcZEKnVgm5AZXWychzkB10nKMjYcYLeAfPkVJwTkrq5g+ILslzSEf5RlXRfOzHQBGBoiaYKY= root@remote-host
   
If at some point in the future, the hash doesn't match, we get a stern warning about a possible man-in-the-middle attack.   
   
Now we need to authenticate the local node to the remote node which we are logging in to.
First we generate generate ssh keys on the local node:

.. code:: bash

   local-node$  ssh-keygen -t rsa -f /home/nthompson/.ssh/id_rsa -N '' -C "MPI Keys"
   Generating public/private rsa key pair.
   Your identification has been saved in /home/nthompson/.ssh/id_rsa.
   Your public key has been saved in /home/nthompson/.ssh/id_rsa.pub.
   The key fingerprint is:
   SHA256:mgjcggMSHCwPh4xXqc1tPcp2ESM+ncOAt/XSG78RBnY MPI Keys

Now we just scp id_rsa.pub over to our remote-node, and we're good right?
No, we aren't, because scp also required ssh!
So we have to find a node that has permissions to ssh into both local and remote, and copy the public key around that way:

.. code:: bash

   priviledged-node$ sftp nthompson@local-node:.ssh
   > get id_rsa.pub
   Fetching /home/nthompson/.ssh/id_rsa.pub to id_rsa.pub
   /home/nthompson/.ssh/id_rsa.pub                                                     100%  398     0.4KB/s   00:00
   > bye
   priviledged-node$ scp id_rsa.pub nthompson@remote-node:.ssh
   priviledged-node$ ssh remote-node
   remote-node$ cd ~/.ssh; cat id_rsa.pub >> authorized_keys
   
This is a super-awkward procedure; is there a better way?

---------------
Standard Images
---------------

If all of our compute nodes launched off the same VM snapshot, then we would be guaranteed that the ssh keys would be in the correct location.
Note that this can also be achieved by mounting networked disks, but we'll get additional wins via a VM snapshot:

.. code:: bash

   $ gcloud compute instances create node-0 --metadata-from-file startup-script=startup.sh \
     --image ubuntu-15-10 --machine-type n1-standard-4 --preemptible --scopes=compute-rw,storage-full
   $ gcloud compute ssh node-0
   node-0$ ssh-keygen -t rsa -f ~/.ssh/id_rsa -N '' -C "MPI Keys"
   node-0$ cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
   node-0$ # Make sure that your MPI executable is on a system path:
   node-0$ sudo cp mpi_hello.x /usr/bin
   
Now we need to snapshot our VM:

.. code:: bash

   $ gcloud compute disks snapshot "node-0" --snapshot-names "mpi-node"
   
 Now we can create a cluster from out snapshot:
 
 .. code:: bash
 
    $ gcloud compute disks create mpi-disk-{1..5}  --source-snapshot "mpi-node"
    $ for i in `seq 1 5`; do gcloud compute instances create mpi-node-$i --disk name=mpi-disk-$i,boot=yes,mode=rw; done;

Now we can ssh from compute node to compute node without any other boilerplate:

.. code:: bash

   mpi-node-1:~$ ssh mpi-node-2
   mpi-node-2:~$ ssh mpi-node-3
   mpi-node-3:~$ ssh mpi-node-4 # ... so on
   
This was a necessary condition for MPI to work; let's see if it's sufficient:

.. code:: bash

   mpi-node-1:~$ mpirun -np 5 --host mpi-node-2,mpi-node-3,mpi-node-4,mpi-node-5 mpi_hello.x
   Hello world from process 3 of 5
   Hello world from process 4 of 5
   Hello world from process 1 of 5
   Hello world from process 2 of 5
   Hello world from process 0 of 5
   
It works!

----------------------------
Automate, automate, automate
----------------------------

Thus far, we've only managed to get MPI to run on our cluster.
We want to advance to *on demand clusters*, and for this we need automation.
To do this, we'll use the gcloud python bindings.
Let's do an example by listing all compute instances and deleting one in our project:

.. code:: bash

   $ sudo apt-get install -y python3-pip libffi-dev libssl-dev
   $ python3.5 -m pip install gcloud google-api-python-client
   $ python3 -q
   >>> from oauth2client.client import GoogleCredentials
   >>> credentials = GoogleCredentials.get_application_default()
   >>> from googleapiclient import discovery
   >>> compute = discovery.build('compute', 'v1', credentials=credentials)
   >>> r = compute.instances().list(project='my_project_id', zone='us-central1-c').execute()
   >>> for i in r['items']:
   ...     print(i['name'])
   instance1
   instance2
   >>> compute.instances().delete(project='my_project_id', zone='us-central1-c', instance='instance1').execute()
   

If you got the following error:

.. code:: bash

   googleapiclient.errors.HttpError: <HttpError 403 when requesting https://www.googleapis.com/compute/v1/projects/my_project_id/zones/us-central1-c/instances?alt=json returned "Insufficient Permission">

then you forget to specify the :code:`--scopes=compute-rw` flag when creating your instance.

Creating an instance is a little more complicated than deleting and listing them.
It's not much better than making a straight POST request to the API endpoint with raw JSON (see the example_ from google).

However, when all is said and done, we can (hopefully) generate our cluster using:

.. code:: bash

   $ ./run_create_cluster.py 'my_project_id' --cluster_name 'clustah' --nodes 3
   

.. _quota: https://docs.google.com/a/google.com/forms/d/1vb2MkAr9JcHrp6myQ3oTxCyBv2c7Iyc5wqIKqE3K4IE/viewform?entry.1036535597&entry.1823281902&entry.1934621431&entry.612627929&entry.666100773&entry.2004330804&entry.1287827925&entry.1005864466&entry.511996332&entry.308842821&entry.1506342651&entry.1193238839=No&entry.1270586847&entry.394661533&entry.1276962733&entry.1256670372&entry.1742484064&entry.15530

.. _example: https://github.com/GoogleCloudPlatform/python-docs-samples/blob/master/compute/api/create_instance.py


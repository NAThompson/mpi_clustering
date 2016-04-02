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

This is a pain; here's a partial solution:

.. code:: bash

   $ echo "StrictHostKeyChecking no" | sudo tee --append /etc/ssh/ssh_config

And then we get a different problem:

.. code:: bash

   $ mpirun -v -np $(nproc) --hostfile hosts.txt mpi_hello.x
   ssh: connect to host mpi-node-1 port 22: Connection timed out
   $ mpirun -np $(nproc) --hostfile hosts.txt mpi_hello.x
   Permission denied (publickey).

.. _quota: https://docs.google.com/a/google.com/forms/d/1vb2MkAr9JcHrp6myQ3oTxCyBv2c7Iyc5wqIKqE3K4IE/viewform?entry.1036535597&entry.1823281902&entry.1934621431&entry.612627929&entry.666100773&entry.2004330804&entry.1287827925&entry.1005864466&entry.511996332&entry.308842821&entry.1506342651&entry.1193238839=No&entry.1270586847&entry.394661533&entry.1276962733&entry.1256670372&entry.1742484064&entry.15530

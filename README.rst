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
    $ gcc -o mpi_hello mpi_hello.o -lmpi
    $ mpirun -np $(nproc) mpi_hello
    Hello world from process 2 of 4
    Hello world from process 3 of 4
    Hello world from process 1 of 4
    Hello world from process 0 of 4

So it works. Now let's create a cluster on gcloud, using the following startup script (call it startup.sh):

.. code:: bash

    #!/bin/bash

    sudo apt-get update
    sudo apt-get install -y libopenmpi-dev openmpi-bin

And let's use this to create a cluster of identical instances:

.. code:: bash

   $ gcloud compute instances create mpi-node-{1..5} --metadata-from-file startup-script=startup.sh \
     --image ubuntu-15-10 --machine-type n1-standard-4 --preemptible --scopes=compute-rw
   ERROR: (gcloud.compute.instances.create) Some requests did not succeed:
   	  - Quota 'CPUS' exceeded.  Limit: 8.0

Whoops! We need to increase our CPU quota limit before proceeding, we need to fill out quota_ change request form. Once this is done, re-run the previous command to obtain you compute nodes.




.. _quota: https://docs.google.com/a/google.com/forms/d/1vb2MkAr9JcHrp6myQ3oTxCyBv2c7Iyc5wqIKqE3K4IE/viewform?entry.1036535597&entry.1823281902&entry.1934621431&entry.612627929&entry.666100773&entry.2004330804&entry.1287827925&entry.1005864466&entry.511996332&entry.308842821&entry.1506342651&entry.1193238839=No&entry.1270586847&entry.394661533&entry.1276962733&entry.1256670372&entry.1742484064&entry.15530

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <mpi/mpi.h>

int main (int argc, char** argv)
{
    int rank, size;

    MPI_Init (&argc, &argv);
    MPI_Comm_rank (MPI_COMM_WORLD, &rank);
    MPI_Comm_size (MPI_COMM_WORLD, &size);
    char hostname[150];
    memset(hostname, 0, 150);
    gethostname(hostname, 150);
    printf( "Hello world from process %d of %d on host %s\n", rank, size, hostname );
    MPI_Finalize();
    return 0;
}

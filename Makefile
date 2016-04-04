all:
	gcc -c mpi_hello.c -o mpi_hello.o
	gcc -o mpi_hello.x mpi_hello.o -lmpi
install:
	cp mpi_hello.x /usr/bin

clean:
	rm -f *.x *.o

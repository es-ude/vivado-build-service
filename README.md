# Vivado Simulation Automation Tool

This tool is designed to automate Vivado simulations by enabling clients to submit their build files to a server over a socket connection.



# Client-side Setup:

Modify the connection configurations in docs/config.py as needed.

Ensure the required Python dependencies are installed by running:

    pip install -r requirements.txt

Run the client with the desired username and build directory:

    python client.py {username} {directory}



# Server-side Setup:

Modify the server configurations in docs/config.py as needed.

Ensure the required Python dependencies are installed by running:

    pip install -r requirements.txt

Setup the environment by running:

    python setup.py

Run the server using:

    python server.py



# Task Handling:

The server handles incoming simulation tasks and distributes them to a task queue.

The taskhandler.py script processes tasks in a separate thread, executing simulations and updating the result directory.
  


# Project Structure

<h3>client.py:</h3>

- Client script for submitting simulation build files to the server.


<h3>server.py:</h3>

- Server script for handling incoming simulation tasks and distributing them to the task queue.


<h3>taskhandler.py:</h3>

- Manages the task queue and executes simulation tasks in a separate thread.


<h3>autobuild_binfile.sh:</h3>

- Bash script for automating Vivado simulations based on the provided build files.



# Dependencies

The simulationflow module includes utility functions for file handling and task processing.

Configuration parameters are specified in docs/config.ini.



# Configuration

Ensure the configurations in docs/config.ini are appropriately set for your environment before running the client and server.


<h2>Paths</h2>

<h3>send:</h3>
  
- The directory path where the client looks for build files to send to the server.


<h3>receive:</h3>

- The directory path where the server expects to receive simulation-related files from the client.


<h3>request:</h3>
    
- The name of the build file that the client sends to the server.


<h3>tcl script:</h3>
  
- The path to the TCL script (create_project_full_run.tcl) used in Vivado simulation.



<h2>Connection</h2>

<h3>chunk size:</h3>
    
- The size of data chunks used during communication between the client and server.


<h3>delimiter:</h3>
  
- A value used to delimit different pieces of data in communication.


<h3>host:</h3>
    
- The hostname or IP address of the server.


<h3>port:</h3>
    
- The port number on which the server listens for incoming connections.



<h2>VNC</h2>

<h3>username:</h3>
  
- The username used for a VNC connection.


<h3>ip address:</h3>
   
- The IP address associated with the VNC connection.



<h2>Database</h2>

<h3>DB URL:</h3>
     
- The URL or connection string for the database.

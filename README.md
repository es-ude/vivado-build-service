# Vivado Simulation Automation Tool

This tool is designed to automate Vivado simulations by enabling clients to submit their build files to a server over a socket connection.

The client sends their build files using the following command:

    python client.py {username} {directory}

# Client-side Setup:

 Ensure the required Python dependencies are installed by running:

    pip install -r requirements.txt

 Run the client with the desired username and build directory:

    python client.py {username} {directory}

# Server-side Setup:

  Modify the server configurations in docs/config.py as needed.

  Run the server using:

    python server.py

# Task Handling:

  The server handles incoming simulation tasks and distributes them to a task queue.

  The taskhandler.py script processes tasks in a separate thread, executing simulations and updating the result directory.

# Project Structure

  client.py:
      
      Client script for submitting simulation build files to the server.

  server.py:
      
      Server script for handling incoming simulation tasks and distributing them to the task queue.

  taskhandler.py:
      
      Manages the task queue and executes simulation tasks in a separate thread.

  autobuild_binfile.sh:
      
      Bash script for automating Vivado simulations based on the provided build files.

# Dependencies

  The simulationflow module includes utility functions for file handling and task processing.

  Configuration parameters are specified in docs/config.py.

# Configuration

Ensure the configurations in docs/config.py are appropriately set for your environment before running the client and server.

# Paths

  send:
  
    The directory path where the client looks for build files to send to the server.

  receive:

    The directory path where the server expects to receive simulation-related files from the client.

  request:
    
    The name of the build file that the client sends to the server.

  tcl script:
  
    The path to the TCL script (create_project_full_run.tcl) used in Vivado simulation.

# Connection

  chunk size:
    
    The size of data chunks used during communication between the client and server.

  delimiter:
  
    A value used to delimit different pieces of data in communication.

  host:
    
    The hostname or IP address of the server.

  port:
    
    The port number on which the server listens for incoming connections.

 # VNC

  username:
  
    The username used for a VNC connection.

  ip address:
   
    The IP address associated with the VNC connection.

 # Database

   DB URL:
     
    The URL or connection string for the database.

# Online-Discussion-Forum

An assignment for COMP3331 (Computer Networks and Applications). **Full marks** were received. The application is based on a client-server model consisting of one server and multiple clients communicating concurrently. Instead of using HTTP, the application applies a custom application protocol.

## Prerequisites

* `python3` should be installed



## Usage

### Start the Server

```shell
python3 server.py server_port admin_passwd
```

The server should accept the following arguments:

* `server_port`: this is the port number which the server will use to communicate with the clients. 
* `admin_passwd` : this is the admin password for theserver.It is required to shut down the server.

### Start the Client

```shell
python3 client.py server_IP server_port
```

The client should accept the following two arguments:

* `server_IP`: the IP address of the machine on which the server is running.
* `server_port`: the port number being used by the server.



## Discussion Forum Operations

Following successful login, the client displays a message to the user informing them of all available commands and prompting to select one command. The following commands are available:

If an invalid command is selected, an error message should be shown to the user and they should be prompted to select one of the available actions.

**Note that, all commands should be upper-case (CRT, MSG, etc.)** . All arguments (if any) are separated by a single white space and will be one word long (except messages which can contain white spaces). 

- **CRT**: Create Thread

  ```shell
  CRT threadtitle
  ```

- **LST**: List Threads

  ```shell
  LST
  ```

- **MSG**: Post Message

  ```
  MSG threadtitle message
  ```

- **DLT**: Delete Message

  ```
  DLT threadtitle messagenumber
  ```

- **RDT**: Read Thread

  ```
  RDT threadtitle
  ```

- **EDT**: Edit Message

  ```
  EDT threadtitle messagenumber message
  ```

- **UPD**: Upload File

  ```
  UPD threadtitle filename
  ```

- **DWN**: Download File

  ```
  DWN threadtitle filename
  ```

- **RMV**: Remove Thread

  ```
  RMV threadtitle
  ```

- **XIT**: Exit

  ```
  XIT
  ```

- **SHT**: Shutdown Server. 

  ```
  SHT admin_password
  ```

  

  

  

  

  

  




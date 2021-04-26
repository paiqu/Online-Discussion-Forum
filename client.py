# Python 3
# Usage: python3 client.py server_IP server_port
import sys
import socket
import json
import os
import select 
import threading
import time

server_IP = sys.argv[1]
server_port = int(sys.argv[2]) 

# boolean to record if the server is down
server_is_down = False

def handle_connection(connection):
    global server_is_down
    global client_socket
    while not server_is_down:
        data = connection.sendall(b"check")
        try:
            reply = connection.recv(1024)
        except ConnectionResetError:
            break
        if not reply:
            server_is_down = True
            # client_socket.close()
            break
        time.sleep(0.2)
    print("\nGoodbye. Server shutting down")
    connection.close()
    os._exit(0)


# create a socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connect to the server
client_socket.connect((server_IP, server_port))
c_socket.connect((server_IP, server_port+1000))

# start a thread to track server's status
c_thread = threading.Thread(target=handle_connection, args=(c_socket,))
c_thread.daemon = True
c_thread.start()


while not server_is_down:
    # get input from the user
    username = input("Enter username: ")
    while not username:
        print("username can't be empty")
        username = input("Enter username: ")
        
    client_socket.sendall(username.encode())
    reply = client_socket.recv(1024).decode("utf-8")
    reply = json.loads(reply)
    reply_type = reply.get('type')

    if reply_type == "True":
        # username exists
        password = input("Enter password: ")
        while not password:
            print("password can't be empty")
            password = input("Enter password: ")
        client_socket.sendall(password.encode())
        
        
    elif reply_type == "Waiting":
        # username dose not exist -> create a new account
        password = input('Enter new password for ' + username + ': ')
        while not password:
            print("password can't be empty")
            password = input('Enter new password for ' + username + ': ')
        client_socket.sendall(password.encode())
    elif reply_type == "False":
        print(f"{username} has already logged in")
        continue

    reply = client_socket.recv(1024).decode("utf-8")
    reply = json.loads(reply)
    reply_type = reply.get('type')
    if reply_type != 'True':  
        print(reply.get('message'))
        continue
    print(reply.get('message'))
    
    print('Welcome to the forum')
    while not server_is_down:
        # print(f"bool now is {server_is_down}")
        # ask the user for command and then send it to the server
        # command = input("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ")
        while True:
            print(
                "Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ",
                end='',
                flush=True
            )

            # if c_socket not in select.select([], [c_socket], [])[1]:
            #     server_is_down = True
            #     break

            command = sys.stdin.readline().strip()
            # command = input("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT, SHT: ")
                
            if not command:
                print("Command can't be empty")
                continue
            break

        command_type = command.split()[0]

        # if UPD -> upload the file to the server
        if command_type == "UPD":
            if len(command.split()) != 3:
                print(f"Incorrect syntax for {command_type}")
                continue
            filename = command.split()[2]
            if not os.path.exists(filename):
                print(f"The file {filename} does not exist")
                continue
            # send the full command to the server
            client_socket.sendall(command.encode())

            # receive the result of checking thread title
            reply = client_socket.recv(1024).decode("utf-8")
            reply = json.loads(reply)
            if reply.get('type') == "False":
                print(reply.get('message'))
                continue
            client_socket.sendall(b"checking filename")
            # Receive the result of checking filename
            reply = client_socket.recv(1024).decode("utf-8")
            reply = json.loads(reply)
            if reply.get('type') == "False":
                print(reply.get('message'))
                continue

            # transfer the file
            filesize = str(os.path.getsize(filename))

            # send the actual file size to the server first
            client_socket.sendall(filesize.encode())
            with open(filename, 'rb') as f:
                data = f.read(1024)
                while data:
                    client_socket.sendall(data)
                    data = f.read(1024)
            reply = client_socket.recv(1024).decode("utf-8")
            reply = json.loads(reply)
            print(reply.get('message'))
            continue

        elif command_type == "DWN":
            if len(command.split()) != 3:
                print(f"Incorrect syntax for {command_type}")
                continue

            # send the full command to the server
            client_socket.sendall(command.encode())

            # receive the result of checking thread title
            reply = client_socket.recv(1024).decode("utf-8")
            reply = json.loads(reply)
            if reply.get('type') == "False":
                print(reply.get('message'))
                continue
            client_socket.sendall(b"checking filename")

            # Receive the result of checking filename
            reply = client_socket.recv(1024).decode("utf-8")
            reply = json.loads(reply)
            if reply.get('type') == "False":
                print(reply.get('message'))
                continue
            client_socket.sendall(b"getting file size")
            filename = command.split()[2]
            # 1. receive the filesize
            filesize = int(client_socket.recv(1024).decode())
            client_socket.sendall(b"downloading the file")
            # 2. receive the file
            with open(filename, 'wb') as f:
                data = client_socket.recv(1204)
                total = len(data)
                while data:
                    f.write(data)
                    if total != filesize:
                        data = client_socket.recv(1204)
                        total += len(data)
                    else:
                        break
            
            print(f"{filename} successfully downloaded")
            client_socket.sendall(b"True")
            continue


        # send the command to the server
        client_socket.sendall(command.encode())

        # receive the reply from the server
        reply = client_socket.recv(1024).decode("utf-8")
        reply = json.loads(reply)

        if reply.get('type') == "False":
            # command is invalid
            print(reply.get('message'))
        else:
            # command is valid
            print(reply.get('message'))

            if command_type == 'XIT' or command_type == 'SHT':
                # client_socket.shutdown(socket.SHUT_RDWR)
                print("closing the socket")
                # client_socket.shutdown(socket.SHUT_RDWR)
                client_socket.close()
                if command_type == 'SHT':
                    server_is_down = True
                    # client_socket.close()
                sys.exit(0)

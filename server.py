# Python 3 
# Usage: python3 server.py server_port admin_passwd
import sys
import socket
import json
import re
import os
import os.path
import threading
import select

AVAIL_COMMANDS = [
    'CRT', 'MSG', 'DLT', 'EDT',
    'LST', 'RDT', 'UPD', 'DWN',
    'RMV', 'XIT', 'SHT'        
]

def check_username(user_name):
    f = open('credentials.txt', 'r')
    
    while True:
        line = f.readline()
        if not line:
            break # end of line is reached
        if len(line.strip()) != 0:
            info = line.split()
            name = info[0]
            # print('curr name is ' + name)
            # print('given name is ' + user_name)
            if name == user_name:
                f.close()
                return True
    f.close()
    return False

def check_password(user_name, user_password):
    f = open('credentials.txt', 'r')
    while True:
        line = f.readline()
        if not line:
            break # end of line is reached
        if len(line.split()) == 2:
            info = line.split()
            name = info[0]
            password = info[1]
            # print(f"{name} -> {password}")
            if name == user_name and password == user_password:
                f.close()
                return True
    f.close()
    return False

def save_account(user_name, user_password):
    text = user_name + ' ' + user_password
    f = open('credentials.txt', 'a')
    f.write(f'\n{text}')
    f.close()

def send_invalid_command(connection, type):
    data = json.dumps({
            'type': 'False',
            'message': f"Incorrect syntax for {type}"
        })
    connection.sendall(data.encode())

def get_num_of_msgs(title):
    count = 0
    with open(title, 'r') as f:
        line = f.readline()   
        while line:
            line = f.readline()
            if "uploaded" not in line:
                count += 1

    return count - 1        

def listenToClient(connection, client_addr):
    global lock
    global shutdown
    global online_users
    global thread_list
    global thread_file_dict
    global addr
    global port
    global admin_passwd

    # print("new thread started")
    while True:
        username = connection.recv(1024).decode("utf-8")

        # check if the username already registered
        if check_username(username):
            # check if that userhame has logged in
            if username in online_users:
                print(f"{username} has already logged in")
                data = json.dumps({
                    'type': "False",
                    'message': f"{username} has already logged in"
                })
                connection.sendall(data.encode())
                continue
            
            data = json.dumps({
                'type': "True",
                'message': f"{username} is ok, waiting for password"
            })
            connection.sendall(data.encode())

            # received the password from the client
            password = connection.recv(1024).decode()
            if not check_password(username, password):
                print("Incorrect password")
                data = json.dumps({
                    'type': "False",
                    'message': "Incorrect password"
                })
                connection.sendall(data.encode())
                continue
        else:
            # new user
            print("New user")
            data = json.dumps({
                'type': "Waiting",
                'message': f"{username} does not exist. Waiting for a new password"
            })
            connection.sendall(data.encode())

            # receve the password from the clienrt
            password = connection.recv(1024).decode()
            save_account(username, password)
            
        # success login
        print(f"{username} successful login")
        # add the logged in user to online users list
        online_users.append(username)
        data = json.dumps({
            'type': "True",
            'message': f"{username} successful login"
        })
        connection.sendall(data.encode())   

        
        # processing command
        while not shutdown:
            try:
                command = connection.recv(1024).decode("utf-8")
            except socket.timeout:
                print("socket TIMEOUT")
                continue
            if not command:
                print(f"{username} disconnect")
                return
            command = command.split()
            command_type = command[0]
            # acquire the lock
            lock.acquire()
            if command_type not in AVAIL_COMMANDS:
                data = json.dumps({
                    'type': "False",
                    'message': "Invalid command"
                })
                connection.sendall(data.encode())
            else:
                if command_type == 'CRT':
                    # Create Thread
                    if len(command) != 2:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        # check for existence
                        thread_title = command[1]
                        if os.path.exists(thread_title):
                            print(f"Thread {thread_title} exists")
                            data = json.dumps({
                                'type': "False",
                                'message': f"Thread {thread_title} exists"
                            })
                        else:
                            f = open(thread_title, 'w')
                            f.write(f'{username}')
                            f.close()
                            # add the created thread to thead list
                            thread_list.append(thread_title)
                            thread_file_dict[thread_title] = []
                            print(f'Thread {thread_title} created')

                            data = json.dumps({
                                'type': "True",
                                'message': f"Thread {thread_title} created"
                            })
                        # send the reply to the client
                        connection.sendall(data.encode())

                elif command_type == 'MSG':
                    # Post Message
                    if len(command) < 3:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        thread_title = command[1]
                        if os.path.exists(thread_title):
                            message = ' '.join(command[2:])
                            message_num = get_num_of_msgs(thread_title)
                            message = f'\n{message_num + 1} {username}: {message}'
                            f = open(thread_title, 'a')
                            f.write(message)
                            f.close()
                            print(f'Message posted to {thread_title} thread')
                            data = json.dumps({
                                'type': "True",
                                'message': f'Message posted to {thread_title} thread'
                            })
                        else:
                            data = json.dumps({
                                'type': "False",
                                'message': f'Thread {thread_title} does not exist'
                            })
                        connection.sendall(data.encode())

                elif command_type == 'DLT':
                    # Delete Message
                    if len(command) != 3:
                        send_invalid_command(connection, command_type)
                    else:
                        thread_title = command[1]
                        try:
                            msg_num = int(command[2])
                        except ValueError:
                            send_invalid_command(connection, command_type)
                            lock.release()
                            continue
                        
                        # check if thread exists
                        if os.path.exists(thread_title):
                            # check if messager number is valid
                            if msg_num <= get_num_of_msgs(thread_title):
                                with open(thread_title, 'r') as f:
                                    lines = f.readlines()
                                
                                msg_to_delete = ""
                                for line in lines:
                                    if "uploaded" not in line and len(line.split()) != 1:
                                        if int(line.split()[0]) == msg_num:
                                            msg_to_delete = line
                            
                                msg_sender = msg_to_delete.split()[1].rstrip(':')
                                # check username
                                if msg_sender == username:
                                    with open(thread_title, 'r') as f:
                                        lines = f.readlines()
                                    # remove the message from the thread
                                    lines.remove(msg_to_delete)
                                    # upate the left messages
                                    new_lines = []
                                    new_lines.append(lines[0].rstrip())

                                    msg_number = 1
                                    for i in range(1, len(lines)):
                                        if "uploaded" not in lines[i]:
                                            line_in_list = lines[i].split()
                                            new_line = f"{msg_number} " + ' '.join(line_in_list[1:])
                                            new_lines.append(new_line)
                                            msg_number += 1
                                        else:
                                            new_lines.append(lines[i].rstrip("\n"))
                                        
                                    with open(thread_title, 'w') as f:
                                        f.write('\n'.join(new_lines))
                                    print("The message has been deleted")
                                    msg_type = "True"
                                    message = "The message has been deleted"
                                else:
                                    # message is posted by other user
                                    print("Message cannot be deleted")
                                    msg_type = "False"
                                    message = f"The message belongs to another user {msg_sender} and cannot be edited"      
                            else:
                                # message number is invalid
                                print("Given message number is invalid")
                                msg_type = "False"
                                message = "Message number is invalid"                            
                        else:
                            # file does not exist
                            print("Incorrect thread specified")
                            msg_type = "False"
                            message = f"Thread {thread_title} does not exist"
                        data = json.dumps({
                            'type': msg_type,
                            'message': message
                        })
                        connection.sendall(data.encode())

                elif command_type == "EDT":
                    # Edit message
                    # EDT threadtitle messagenumber message
                    # check command format
                    if len(command) < 4:
                        send_invalid_command(connection, command_type)
                        lock.release()
                        continue
                    
                    thread_title = command[1]
                    try:
                        msg_num = int(command[2])
                    except ValueError:
                        send_invalid_command(connection, command_type)
                        selServer.lock.release()
                        continue

                    new_msg = ' '.join(command[3:])
                    # check if thread exists
                    if not os.path.exists(thread_title):
                        print(f"Thread {thread_title} does not exist")
                        data = json.dumps({
                            'type': "False",
                            'message': f"Thread {thread_title} does not exist"
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    # check if message number is valid
                    if msg_num > get_num_of_msgs(thread_title):
                        print("Given message number is invalid")
                        data = json.dumps({
                            'type': "False",
                            'message': "Message number is invalid"
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    # check if the username had posted this message
                    print(username + f" issued {command_type} command")
                    with open(thread_title, 'r') as f:
                        lines = f.readlines()
                    
                    msg_to_change = ""
                    for line in lines:
                        if "uploaded" not in line and len(line.split()) != 1:
                            if int(line.split()[0]) == msg_num:
                                msg_to_change = line
                    
                    msg_sender = msg_to_change.split()[1].rstrip(':')
                    if msg_sender != username:
                        print("Message cannot be edited")
                        msg_type = "False"
                        message = f"The message belongs to another user {msg_sender} and cannot be edited"
                        data = json.dumps({
                            'type': msg_type,
                            'message': message
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    # edit the message
                    index = lines.index(msg_to_change)
                    new_msg = f"{msg_num} {username}: {new_msg}\n"
                    lines[index] = new_msg
                    with open(thread_title, 'w') as f:
                        f.write(''.join(lines).rstrip())
                    print("Message has been edited")
                    data = json.dumps({
                        'type': "True",
                        'message': "The message has been edited"
                    })
                    connection.sendall(data.encode())
                elif command_type == 'LST':
                    # List Threads
                    if len(command) != 1:
                        # There should be no arguments for this command
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        if not thread_list:
                            data = json.dumps({
                                'type': "True",
                                'message': "No threads to list"
                            })
                        else:
                            # list the title of all threads
                            message = '\n'.join(thread_list)
                            # message = ''
                            # for t in thread_list:
                            #     message += f'{t}\n'
                            data = json.dumps({
                                'type': "True",
                                'message': message
                            })     
                        connection.sendall(data.encode())

                elif command_type == 'RDT':
                    # Read Thread
                    if len(command) != 2:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        thread_title = command[1]
                        if os.path.exists(thread_title):
                            f = open(thread_title, 'r')
                            lines = f.readlines()[1:]
                            f.close()
                            message = "".join(lines)
                            # if get_num_of_msgs(thread_title) == 0:
                            if len(lines) == 0:
                                message = f"Thread {thread_title} is empty"

                            data = json.dumps({
                                'type': "True",
                                'message': message
                            })
                            print(f"Thread {thread_title} read")
                        else:
                            print("Incorrect thread specified")
                            data = json.dumps({
                                'type': "False",
                                'message': f'Thread {thread_title} does not exist'
                            })
                        connection.sendall(data.encode())
                elif command_type == 'UPD':
                    # Upload file
                    if len(command) != 3:
                        send_invalid_command(connection, command_type)
                        continue
        
                    print(username + f" issued {command_type} command")
                    thread_title = command[1]
                    filename = command[2]

                    # check if the thread exists
                    if not os.path.exists(thread_title):
                        print(f"Thread {thread_title} does not exist")
                        data = json.dumps({
                            'type': "False",
                            'message': f"Thread {thread_title} does not exist"
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    data = json.dumps({
                        'type': "True",
                        'message': "Thread title checked"
                    })
                    connection.sendall(data.encode())
                    connection.recv(1024)

                    # check if the file not exist
                    if os.path.exists(f"{thread_title}-{filename}"):
                        print(f"{filename} already exists in this thread")
                        data = json.dumps({
                            'type': "False",
                            'message': f"{filename} already exists"
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    data = json.dumps({
                        'type': "True",
                        'message': "Filename checked"
                    })
                    connection.sendall(data.encode())
                    

                    # start to receive the file from the sender
                    # receving filesize first!
                    filesize = int(connection.recv(1024).decode())
                    with open(f"{thread_title}-{filename}", 'wb') as f:
                        file_data = connection.recv(1024)
                        total = len(file_data)
                        while file_data:
                            f.write(file_data)
                            if total != filesize:
                                file_data = connection.recv(1024)
                                total += len(file_data)
                            else:
                                break
                            
                    print(f"{username} uploaded {filename} to {thread_title} thread")
                    thread_file_dict[thread_title].append(filename)
                    data = json.dumps({
                        'type': "True",
                        'message': f"{filename} uploaded to {thread_title} thread"
                    })

                    # update thread entry
                    with open(thread_title, 'a') as f:
                        f.write(f"\n{username} uploaded {filename}")
                    connection.sendall(data.encode())
                elif command_type == 'DWN':
                    # Download file
                    # DWN threadtitle filename
                    # check command format
                    if len(command) != 3:
                        send_invalid_command(connection, command_type)
                        lock.release()
                        continue

                    print(f"{username} issued {command_type} command")
                    thread_title = command[1]
                    filename = command[2]
                    
                    # check if the thread exists
                    if not os.path.exists(thread_title):
                        print(f"Thread {thread_title} does not exist")
                        data = json.dumps({
                            'type': "False",
                            'message': f"Thread {thread_title} does not exist"
                        })
                        connection.sendall(data.encode())
                        lock.release()   
                        continue
                    data = json.dumps({
                        'type': "True",
                        'message': "Thread title checked"
                    })  
                    connection.sendall(data.encode())

                    connection.recv(1024)
                    # check if the file was uploaded to the thread
                    if not os.path.exists(f"{thread_title}-{filename}"):
                        print(f"{filename} does not exist in Thread {thread_title}")
                        data = json.dumps({
                            'type': "False",
                            'message': f"File does not exist in Thread {thread_title}"
                        })
                        connection.sendall(data.encode())
                        lock.release()
                        continue
                    data = json.dumps({
                        'type': "True",
                        'message': "Filename checked"
                    })
                    connection.sendall(data.encode())
                    
                    connection.recv(1024)

                    # transfer the file to the client
                    # 1. send the size of the file
                    thread_filename = f"{thread_title}-{filename}"
                    filesize = str(os.path.getsize(thread_filename))
                    connection.sendall(filesize.encode())

                    connection.recv(1024)

                    # 2. transfer the file
                    with open(thread_filename, 'rb') as f:
                        file_data = f.read(1024)
                        while file_data:
                            connection.sendall(file_data)
                            file_data = f.read(1024)
                    reply = connection.recv(1024).decode()
                    if reply == "True":
                        print(f"{filename} downloaded from Thread 3331")
                    else:
                        print("Downloading fails")
                elif command_type == 'RMV':
                    # Remove Thread
                    if len(command) != 2:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        thread_title = command[1]
                        if os.path.exists(thread_title):
                            # file exists
                            # check user name
                            with open(thread_title) as f:
                                first_line = f.readline().strip()
                            if username == first_line:
                                thread_list.remove(thread_title)
                                del thread_file_dict[thread_title]
                                os.remove(thread_title)
                                msg_type = 'True'
                                message = f"Thread {thread_title} removed"
                                print(message)
                            else:
                                print(f"Thread {thread_title} cannot be removed")
                                msg_type = 'False'
                                message = f"The thread was create by another user and cannot be removed"
                            data = json.dumps({
                                'type': msg_type,
                                'message': message
                            })
                        else:
                            print("Incorrect thread specified")
                            data = json.dumps({
                                'type': "False",
                                'message': f"Thread {thread_title} does not exist"
                            })
                        connection.sendall(data.encode())
                elif command_type == 'XIT':
                    # Exit
                    if len(command) != 1:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + " exited")
                        # remove the user from online users
                        online_users.remove(username)
                        data = json.dumps({
                            'type': "True",
                            'message': "Goodbye"
                        })
                        connection.sendall(data.encode())

                        # close connection
                        connection.close()
                        lock.release()

                        return
                        
                elif command_type == 'SHT':
                    # Shutdown
                    if len(command) != 2:
                        send_invalid_command(connection, command_type)
                    else:
                        print(username + f" issued {command_type} command")
                        password = command[1]
                        if password == admin_passwd:   
                            print("Server shutting down")
                            msg_type = "True"
                            message = "Goodbye. Server shutting down"

                            # remove thread and its stored files
                            for t in thread_list:
                                os.remove(t)
                                files = thread_file_dict[t]
                                for f in files:
                                    os.remove(f"{t}-{f}")
                            # remove the credentials.txt
                            os.remove("credentials.txt")
                            thread_list.clear()
                            data = json.dumps({
                                'type': msg_type,
                                'message': message
                            })
                            connection.sendall(data.encode())
                            
                            shutdown = True
                            
                            connection.close()
                            lock.release()
                            
                            return
                        else:
                            msg_type = "False"
                            message = "Incorrect password"
                            print(message)
                            data = json.dumps({
                                'type': msg_type,
                                'message': message
                            })
                            connection.sendall(data.encode())
            # release the lock
            lock.release()
        
def connection_check(connection, client_addr):
    global shutdown
    global c_lock
    while not shutdown:
        # print('entering while loop')
        c_lock.acquire()
        data = connection.recv(1024)
        if not data:
            break
        message = connection.sendall(b"True")
        c_lock.release()

if __name__ == "__main__":
    # new code
    addr = '127.0.0.1'
    # get port number
    port = int(sys.argv[1])

    # get admin's password
    admin_passwd = sys.argv[2]

    # attributes for the server
    lock = threading.Lock()
    c_lock = threading.Lock()
    shutdown = False
    
    # lists to store clients' data
    online_users = []
    thread_list = []
    thread_file_dict = {}
    running_threads = []
    # running_threads = []
    # create the server's socket and set it as reusable
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((addr, port))
    sock.listen(3)
    print('Waiting for clients')

    # # this socket is used by the client to check if the server is down
    c_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    c_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    c_sock.bind((addr, port+1000))
    c_sock.listen(5)

    # accept client's connection_socket connection first
    (c_connection, c_addr) = c_sock.accept()
    # connection, client_addr = sock.accept()
    connection_check = threading.Thread(target=connection_check, args=(c_connection, c_addr)) 
    connection_check.start()

    
    # sock.settimeout(0.1)
    

    # try:
    while not shutdown:
        r, _, _ = select.select([sock], [], [], 5)
        if sock in r:
            connection, client_addr = sock.accept()
            # connection.settimeout(60)
            client = threading.Thread(target=listenToClient, args=(connection, client_addr))
            client.daemon = True
            running_threads.append(client)
            client.start()
    # finally:
    sock.close()    
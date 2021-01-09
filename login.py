import pymysql
import socket
import re
from _thread import *
import sys


def check_if_user_exists(username, password):
    """
    This function checks whether the record with such username and password exists in db
    :param username: the username of the chat user
    :param password: the password of the chat user
    :return: True, if record exists, False if not
    """
    conn = pymysql.connect(host="127.0.0.1", user="chat", password="chat", database="chat", port=3306)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = %s and password = %s", (username, password))

    if cursor.fetchone() is not None:
        print(username + " " + password + " exists")
        return True

    print(username + " " + password + " does not exist")
    conn.close()
    return False


def client_thread(conn, addr):
    username_password = conn.recv(2048)
    action, user, passwd = re.split('\s+', username_password.decode('utf-8'))
    if action == 'l':
        if check_if_user_exists(user, passwd):
            conn.send(b"true")
        else:
            conn.send(b"false")

    if action == 's':
        if check_if_user_exists(user, passwd):
            conn.send(b"exists")
        else:
            db = pymysql.connect(host="127.0.0.1", user="chat", password="chat", database="chat", port=3306)
            cursor = db.cursor()
            cursor.execute("INSERT INTO users(username, password, login) VALUES (%s, %s, %s)", (user, passwd, True))
            db.commit()
            print(user + " " + passwd + " added")
            conn.send(b"added")
            db.close()

    remove(conn)


# set the connection to database
conn = pymysql.connect(host="127.0.0.1", user="chat", password="chat", database="chat", port=3306)
cursor = conn.cursor()

# create the table with appropriate columns
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
  id INT(4) UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(30),
  password VARCHAR(30),
  login BOOLEAN
) engine=InnoDB;""")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
"""
the first argument AF_INET is the address domain of the socket. This is used when we have an Internet Domain
with any two hosts
The second argument is the type of socket. SOCK_STREAM means that data or characters are read in a continuous flow
"""
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
if len(sys.argv) != 3:
    print("Correct usage: script, IP address, port number")
    exit()

IP_address = str(sys.argv[1])
Port = int(sys.argv[2])
server.bind((IP_address, Port))

# binds the server to an entered IPaddress and at the specified port number.The client must be aware of these parameters
server.listen(100)

# listens for 100 active connections. This number can be increased as per convenience
list_of_clients = []


def remove(connection):
    if connection in list_of_clients:
        list_of_clients.remove(connection)


while True:
    conn, addr = server.accept()
    """
    Accepts a connection request and stores two parameters, conn which is a socket object for that user,
    and addr which contains
    the IP address of the client that just connected
    """
    list_of_clients.append(conn)
    print(addr[0] + " connected")
    # maintains a list of clients for ease of broadcasting a message to all available people in the chatroom
    # Prints the address of the person who just connected
    start_new_thread(client_thread, (conn, addr))
    # creates and individual thread for every user that connects

server.close()
conn.close()

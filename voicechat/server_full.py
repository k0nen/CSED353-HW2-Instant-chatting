#!/usr/bin/env python3
import socket
from threading import Thread


def accept_text():
	while True:
		client, client_address = SERVER_TEXT.accept()
		print("%s:%s has connected." % client_address)
		client.send(bytes("Type your name and press enter!", "utf8"))
		addresses_text[client] = client_address
		Thread(target=handle_client_text, args=(client,)).start()


def accept_voice():
	while True:
		client, client_address = SERVER_VOICE.accept()
		addresses_voice[client] = client_address
		Thread(target=handle_client_voice, args=(client,)).start()
		print('voice OK')


def handle_client_text(client):
	name = client.recv(BUFSIZ).decode("utf8")
	welcome = 'Welcome %s! If you ever want to quit, type {quit} to exit.' % name
	client.send(bytes(welcome, "utf8"))
	msg = "%s has joined the chat!" % name
	broadcast(bytes(msg, "utf8"))
	clients_text[client] = name

	while True:
		msg = client.recv(BUFSIZ)
		if msg != bytes("{quit}", "utf8"):
			broadcast(msg, name + ": ")
		else:
			client.send(bytes("{quit}", "utf8"))
			client.close()
			erase_client(client)
			broadcast(bytes("%s has left the chat." % name, "utf8"))
			break


def handle_client_voice(client):
	clients_voice[client] = 1
	while client in clients_voice:
		data = client.recv(1024)
		broadcast(data, dtype='voice')


def erase_client(client):
	del clients_text[client]
	del addresses_text[client]
	del clients_voice[client]
	del addresses_voice[client]


def broadcast(msg, prefix="", dtype='text',):
	if dtype == 'text':
		for sock in clients_text:
			sock.send(bytes(prefix, "utf8") + msg)
	else:  # dtype == 'voice'
		for sock in clients_voice:
			sock.send(msg)


# Main execution route
clients_text = {}
addresses_text = {}
clients_voice = {}
addresses_voice = {}

HOST = ''
PORT_TEXT = 1025
PORT_VOICE = 50007
BUFSIZ = 1024
ADDR_TEXT = (HOST, PORT_TEXT)
ADDR_VOICE = (HOST, PORT_VOICE)

SERVER_TEXT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_TEXT.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_TEXT.bind(ADDR_TEXT)

SERVER_VOICE = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_VOICE.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_VOICE.bind(ADDR_VOICE)

if __name__ == "__main__":
	SERVER_TEXT.listen(5)
	SERVER_VOICE.listen(5)
	print("Waiting for connection...")

	ACCEPT_THREAD_TEXT = Thread(target=accept_text)
	ACCEPT_THREAD_TEXT.start()

	ACCEPT_THREAD_VOICE = Thread(target=accept_voice)
	ACCEPT_THREAD_VOICE.start()
	ACCEPT_THREAD_VOICE.join()
	ACCEPT_THREAD_TEXT.join()
	SERVER_TEXT.close()
	SERVER_VOICE.close()

#!/usr/bin/env python3
import socket
from threading import Thread
import threading

# Text socket manager, assign a thread to each connection
def accept_text():
	while True:
		client, client_address = SERVER_TEXT.accept()
		print("%s:%s has connected." % client_address)
		client.send(bytes("Type your name and press enter!", "utf8"))
		Thread(target=handle_client_text, args=(client,)).start()


# Voice socket manager, assign a thread to each connection
def accept_voice():
	while True:
		client, client_address = SERVER_VOICE.accept()
		Thread(target=handle_client_voice, args=(client,)).start()
		print('Voice OK')


# Video socket manager, assign a thread to each connection
def accept_video():
	while True:
		client, client_address = SERVER_VIDEO.accept()
		Thread(target=handle_client_video, args=(client,)).start()
		print("Video OK")


# Main text message handler for each client
# The first recv() is for name, then it will broadcast the messages received until {quit}.
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


# Main voice message handler for each client
# Will broadcast the voice snippet to every client
def handle_client_voice(client):
	clients_voice[client] = 1
	while client in clients_voice:
		try:
			data = client.recv(1024)
			broadcast(data, dtype='voice', sd=client)
		except Exception as _:
			client.close()
			del clients_voice[client]


# Main video handler for each client
def handle_client_video(client):
	clients_video[client] = 1
	while client in clients_video:
		#try:
		totrec = 0
		metarec = 0
		msgArray = []
		metaArray = []

		while metarec < 8:
			chunk = client.recv(8 - metarec)
			metaArray.append(chunk)
			metarec += len(chunk)

		length = int(chunk.decode("utf8"))

		while totrec < length:
			chunk = client.recv(length-totrec)
			if chunk == '':
				raise RuntimeError("Socket connection broken")
			msgArray.append(chunk)
			totrec += len(chunk)


		broadcast(b''.join(metaArray+msgArray), dtype="video",sd=client)

		#except Exception as _:
		#	print('fuck!')
		#	client.close()
		#	del clients_video[client]


# Delete a text socket from client list
def erase_client(client):
	del clients_text[client]
	del clients_voice[client]
	del clients_video[client]


# Broadcast a message to every client, depends on voice or text
def broadcast(msg, prefix="", dtype='text', sd=None):
	if dtype == 'text':
		for sock in clients_text:
			sock.send(bytes(prefix, "utf8") + msg)
	elif dtype == 'voice':
		for sock in clients_voice:
			if sd != sock:
				sock.send(msg)
	elif dtype == 'video':
		for sock in clients_video:
			if sd != sock:
				sock.send(msg)


# Main execution route
clients_text = {}
clients_voice = {}
clients_video = {}

HOST = ''
PORT_TEXT = 1025
PORT_VOICE = 50007
PORT_VIDEO = 1026

BUFSIZ = 1024

ADDR_TEXT = (HOST, PORT_TEXT)
ADDR_VOICE = (HOST, PORT_VOICE)
ADDR_VIDEO = (HOST, PORT_VIDEO)

SERVER_TEXT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_TEXT.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_TEXT.bind(ADDR_TEXT)

SERVER_VOICE = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_VOICE.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_VOICE.bind(ADDR_VOICE)

SERVER_VIDEO = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_VIDEO.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_VIDEO.bind(ADDR_VIDEO)

if __name__ == "__main__":
	SERVER_TEXT.listen(5)
	SERVER_VOICE.listen(5)
	SERVER_VIDEO.listen(5)
	print("Waiting for connection...")

	ACCEPT_THREAD_TEXT = Thread(target=accept_text).start()

	ACCEPT_THREAD_VOICE = Thread(target=accept_voice).start()

	ACCEPT_THREAD_VIDEO = Thread(target=accept_video()).start()

	ACCEPT_THREAD_VOICE.join()
	ACCEPT_THREAD_TEXT.join()
	ACCEPT_THREAD_VIDEO.join()

	SERVER_TEXT.close()
	SERVER_VOICE.close()
	SERVER_VIDEO.close()

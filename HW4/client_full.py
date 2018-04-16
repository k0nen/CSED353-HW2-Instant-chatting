#!/usr/bin/env python3
import socket
from threading import Thread
import pyaudio
from ctypes import *
import tkinter
import sys

# Audio quality
CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WIDTH = 2
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)


# This handler prevents the ALSA debug information from spamming stdout
def py_error_handler(filename, line, function, err, fmt):
	pass


# PyAudio configurations
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
asound = cdll.LoadLibrary('libasound.so.2')
asound.snd_lib_error_set_handler(c_error_handler)
p = pyaudio.PyAudio()
stream_send = p.open(
	format=pyaudio.paInt16,
	channels=CHANNELS,
	rate=RATE,
	input=True,
	frames_per_buffer=CHUNK)
stream_recv = p.open(
	format=p.get_format_from_width(WIDTH),
	channels=CHANNELS,
	rate=RATE,
	output=True,
	frames_per_buffer=CHUNK)


# Text receive thread, print any message received
def receive_text():
	while True:
		try:
			msg = client_socket_text.recv(BUFSIZ).decode("utf8")
			msg_list.insert(tkinter.END, msg)
		except OSError:
			break


# Voice receive thread, print any voice snippet received
def receive_voice():
	while True:
		try:
			data = client_socket_voice.recv(BUFSIZ)
			stream_recv.write(data)
		except OSError:
			break


# Text sending thread, sends this client's message to server
# If the user writes {quit}, then close connection
def send_text():
	msg = my_msg.get()
	client_socket_text.send(bytes(msg, "utf8"))
	if msg == "{quit}":
		client_socket_text.close()
		client_socket_voice.close()
		quit()
	my_msg.set("")


# Voice sending thread, sends voice chunk everytime the buffer gets full
def send_voice():
	while True:
		try:
			data = stream_send.read(CHUNK)
			client_socket_voice.sendall(data)
		except OSError:
			break
# Executed when window is closed
def on_closing(event=None):
	my_msg.set("{quit}")
	send_text()

# tkinter setting
top = tkinter.Tk()
top.title("CSED353 chatting program")

messages_frame = tkinter.Frame(top)
my_msg = tkinter.StringVar()
my_msg.set("Type your messages here")

scrollbar = tkinter.Scrollbar(messages_frame)

msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.LEFT, fill=tkinter.BOTH)
msg_list.pack()
messages_frame.pack()

entry_field = tkinter.Entry(top, textvariable=my_msg)
entry_field.bind("<Return>", send_text)
entry_field.pack()

send_button = tkinter.Button(top, text="Send", command=send_text)
send_button.pack()

top.protocol("WM_DELETE_WINDOW", on_closing)



# Main execution route
try:
	HOST = sys.argv[1]
except IndexError:
	print("Usage: ./client [HOST]")
	quit()

PORT_TEXT = 1025
PORT_VOICE = 50007

BUFSIZ = 1024
ADDR_TEXT = (HOST, PORT_TEXT)
ADDR_VOICE = (HOST, PORT_VOICE)

client_socket_text = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_text.connect(ADDR_TEXT)
client_socket_voice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_voice.connect(ADDR_VOICE)

receive_text_thread = Thread(target=receive_text)
receive_text_thread.start()

receive_voice_thread = Thread(target=receive_voice)
receive_voice_thread.start()

send_voice_thread = Thread(target=send_voice).start()

tkinter.mainloop()

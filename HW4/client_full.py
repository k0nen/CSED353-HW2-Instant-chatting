#!/usr/bin/env python3
import socket
from threading import Thread
import pyaudio
from ctypes import *
import tkinter
import sys
import threading
from PIL import Image
from PIL import ImageTk
import cv2
import io
import numpy

# Audio quality
CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WIDTH = 2
ERROR_HANDLER_FUNC = CFUNCTYPE(None, c_char_p, c_int, c_char_p, c_int, c_char_p)

# Needed for webcam
cap = cv2.VideoCapture(0)

# This handler prevents the ALSA debug information from spamming stdout
def py_error_handler(filename, line, function, err, fmt):
	pass

# PyAudio configurations
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
#asound = cdll.LoadLibrary('libasound.so.2')
#asound.snd_lib_error_set_handler(c_error_handler)
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

def receive_video():
	global panel
	while not stop_video.is_set():
		try:
			totrec = 0
			metarec = 0

			msgArray = []
			metaArray = []

			while metarec < 8:
				chunk = client_socket_video.recv(8 - metarec).decode("utf8")
				if chunk == '':
					raise RuntimeError("Socket connection broken")
				metaArray.append(chunk)
				metarec += len(chunk)

			lengthstr = ''.join(metaArray)
			length = int(lengthstr)

			while totrec < length:
				chunk = client_socket_video.recv(length - totrec)
				if chunk == '':
					raise RuntimeError("Socket connection broken")
				msgArray.append(chunk)
				totrec += len(chunk)

			frame = b''.join(msgArray)
			pil_bytes = io.BytesIO(frame)
			pil_image = Image.open(pil_bytes)
			image = ImageTk.PhotoImage(pil_image)

			if panel is None:
				panel = tkinter.Label(video_frame, image=image)
				panel.image = image
				panel.pack(side=tkinter.TOP, expand=True)


			# Otherwise, simply update the panel
			else:
				panel.configure(image=image)
				panel.image = image

		except OSError:
			break


# Text sending thread, sends this client's message to server
# If the user writes {quit}, then close connection
def send_text(a=1):
	msg = my_msg.get()
	client_socket_text.send(bytes(msg, "utf8"))
	if msg == "{quit}":
		client_socket_text.close()
		client_socket_voice.close()
		top.destroy()
		top.quit()
		stop_video.set()
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


# Video sending thread, sends video chunk in real time
def send_video():
	global cap

	while not stop_video.is_set():
		ret_val, img = cap.read()
		img = cv2.resize(img, (360, 360))

		# cv2.imshow('my webcam', img)
		cv2_im = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		pil_im = Image.fromarray(cv2_im)
		b = io.BytesIO()
		pil_im.save(b, 'jpeg')
		framestring = b.getvalue()

		totalsent = 0
		metasent = 0
		length = len(framestring)
		lengthstr = str(length).zfill(8)

		while metasent < 8:
			sent = client_socket_video.send(lengthstr[metasent::].encode("utf8"))
			if sent == 0:
				raise RuntimeError("Socket connection broken")
			metasent += sent

		while totalsent < length:
			sent = client_socket_video.send(framestring[totalsent::])
			if sent == 0:
				raise RuntimeError("Socket connection broken")
			totalsent += sent

# Executed when window is closed
def on_closing(event=None):
	my_msg.set("{quit}")
	send_text(1)

# Pull webcam video to screen
def show_my_video():
	global cap
	panel = None

	while not stop_video.is_set():
		ret_val, img = cap.read()
		img = cv2.resize(img, (120, 120))

		image = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
		image = Image.fromarray(image)
		image = ImageTk.PhotoImage(image)

		if panel is None:
			panel = tkinter.Label(image=image)
			panel.image = image
			panel.place(height=110, width=110,x=256,y=5)

		else:
			panel.configure(image=image)
			panel.image = image


# tkinter setting
top = tkinter.Tk()
top.title("CSED353 chatting program")

video_frame = tkinter.Frame(top)
video_frame.pack(side=tkinter.TOP)

messages_frame = tkinter.Frame(top)
messages_frame.pack(side=tkinter.TOP)

button_frame = tkinter.Frame(top)
button_frame.pack(side=tkinter.TOP)

my_msg = tkinter.StringVar()
my_msg.set("Type your name here")

scrollbar = tkinter.Scrollbar(messages_frame)

entry_field = tkinter.Entry(button_frame, textvariable=my_msg)
entry_field.bind("<Return>", send_text)
entry_field.pack(side=tkinter.LEFT,padx=10)

send_button = tkinter.Button(button_frame, text="Send", command=send_text)
send_button.pack(side=tkinter.LEFT,padx=10)

send_button = tkinter.Button(button_frame, text="Made by k0nen & gnu", command=send_text)
send_button.pack(side=tkinter.LEFT,padx=10)

msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.TOP, fill=tkinter.BOTH)



top.protocol("WM_DELETE_WINDOW", on_closing)

# Main execution route
try:
	HOST = sys.argv[1]
except IndexError:
	print("Usage: ./client [HOST]")
	quit()

PORT_TEXT = 1025
PORT_VOICE = 50007
PORT_VIDEO =1026

BUFSIZ = 1024

ADDR_TEXT = (HOST, PORT_TEXT)
ADDR_VOICE = (HOST, PORT_VOICE)
ADDR_VIDEO = (HOST, PORT_VIDEO)

# For video
panel = None

stop_video = threading.Event()

client_socket_text = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_text.connect(ADDR_TEXT)
client_socket_voice = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_voice.connect(ADDR_VOICE)
client_socket_video = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket_video.connect(ADDR_VIDEO)

receive_text_thread = Thread(target=receive_text).start()

receive_voice_thread = Thread(target=receive_voice).start()

send_voice_thread = Thread(target=send_voice).start()

send_video_thread = Thread(target=send_video).start()

receive_video_thread = Thread(target=receive_video).start()

show_myvideo_thread = Thread(target=show_my_video).start()

tkinter.mainloop()

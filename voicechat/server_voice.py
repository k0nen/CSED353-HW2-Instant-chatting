# Echo server program
# Based on PyAudio emample
# http://people.csail.mit.edu/hubert/pyaudio/docs/
import socket
import pyaudio

CHUNK = 8192
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
WIDTH = 2
SILENCE = chr(0) * CHUNK * CHANNELS

p = pyaudio.PyAudio()
stream = p.open(
	format=p.get_format_from_width(WIDTH),
	channels=CHANNELS,
	rate=RATE,
	output=True,
	frames_per_buffer=CHUNK)


HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 50007              # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print('Connected by', addr)
data = conn.recv(1024)

while data != '':
		data = conn.recv(1024)
		stream.write(data)


stream.stop_stream()
stream.close()
p.terminate()
conn.close()

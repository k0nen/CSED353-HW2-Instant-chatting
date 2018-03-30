# Simple text/voice chatting program
> CSED353 Computer Network Assignment 3
> 20160832 김근우
> 20160360 명성현
> 


## 1. Environment and Dependencies
이 프로그램은 Python 3.6, Ubuntu 16.04 64비트 환경에서 제작했다. 다른 환경에서는 의도한대로 작동하지 않을 수 있다.


## 2. How to execute
프로그램은 `client_full.py`와 `server_full.py`로 구성되어 있다. 서버는 클라이언트들 사이의 연결을 관리할 뿐, 채팅에 실제로 참여하지는 않는다. 
```shell
ubuntu@ubuntu:$ python server_full.py
Waiting for connection...
```
클라이언트를 실행하면 서버의 IP주소를 입력받는다. 그후 자신의 이름을 입력하면 텍스트/음성 채팅을 사용할 수 있다.
```shell
ubuntu@ubuntu:$ python client_full.py
Enter host: 127.0.0.1
Type your name and press enter!
Foo
Welcome Foo! If you ever want to quit, type {quit} to exit.
Foo: Hello, I am Foo!
```
다른 클라이언트의 접속과 채팅, 접속 종료는 아래처럼 표시된다. 클라이언트가 접속을 종료하고 싶으면 `{quit}`을 입력해서 언제든 종료할 수 있다. 접속을 종료할 때까지 모든 클라이언트는 모든 다른 클라이언트들의 음성을 들을 수 있다.
```shell
Foo: Hello, I am Foo!
Bar has joined the chat!
Bar: Hello, I am Bar!
Bar: I will leave now, bye~
Bar has left the chat.
```

## 3. Code
### 1. Text chatting section
__client__
text chat port는 1025를 사용했다.
```python=
def receive_text():
    while True:
        try:
            msg = client_socket_text.recv(BUFSIZ).decode("utf8")
            print(msg)
        except OSError:
            break

```
client program은 reveive_text()함수를 사용해서 다른 유저로부터의 메세지를 서버로부터 전송받는다. 해당 함수는 thread를 통해 realtime으로 실행된다.
```python=
def send_text():
    while True:
        msg = input()
        print('\033[A\033[A')
        client_socket_text.send(bytes(msg, "utf8"))
        if msg == "{quit}":
            client_socket_text.close()
            client_socket_voice.close()
            quit()

```
send_text()를 통해서 메세지를 전송할 수 있다. 메세지를 입력하면 터미널 상의 한줄을 지워서 인터페이스를 조절했다. {quit}이 입력되는 경우 text chat의 socket뿐만 아니라 voice chat의 socket을 close해주고 종료한다.
__server__
```python=
def accept_text():
    while True:
        client, client_address = SERVER_TEXT.accept()
        print("%s:%s has connected." % client_address)
        client.send(bytes("Type your name and press enter!", "utf8"))
        addresses_text[client] = client_address
        Thread(target=handle_client_text, args=(client,)).start()


```
accept_text()는 client로부터 오는 connect를 accept해주는 함수이다. 이 함수는 thread로 실행이되고 accept를 하면 해당 client를 handling하는 thread를 생성해주고 다시 connection을 기다린다.
```python=
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

```
handle_client_text()는 해당하는 client를 담당하는 함수이다. 이또한 thread로 구현된다. handle_client_text()는 해당하는 client로 부터 메세지를 받아 나머지 connect된 client들에게 broadcasting해준다.

### 2. Voice chatting section
__client__
PyAudio 라이브러리는 마이크로부터 입력을 받아오고, 스피커로 출력을 내보내는 기능을 지원한다. 이를 위해서 입/출력 스트림을 먼저 선언해줘야 한다.
```python=
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
```
클라이언트가 처리해야 할 음성 관련 활동은 두가지이다. 먼저 자신의 마이크를 녹음해서 서버로 보내야 하고, 서버에서 보내준 다른 클라이언트들의 소리도 재생할 수 있어야 한다. 각각을 하나의 함수로 만들고 스레드로 동시에 실행하는 방식을 사용했다.
```python=
def receive_voice():
	while True:
		try:
			data = client_socket_voice.recv(BUFSIZ)
			stream_recv.write(data)
		except OSError:
			break
            
def send_voice():
	while True:
		try:
			data = stream_send.read(CHUNK)
			client_socket_voice.sendall(data)
		except OSError:
			break
```
__server__
서버는 클라이언트들이 어떤 내용을 주고받는지에는 관심이 없다. 내용에 상관없이, 그저 한 클라이언트에서 온 음성 데이터를 모든 클라이언트에게 뿌려주기만 하면 된다. 클라이언트들의 목록을 관리하기 위해, 처음 소켓 연결을 만들 때 클라이언트들의 목록을 `dict`에 추가했다.
```python=
def accept_voice():
	while True:
		client, client_address = SERVER_VOICE.accept()
		addresses_voice[client] = client_address
		Thread(target=handle_client_voice, args=(client,)).start()
		print('voice OK')
```
다만 클라이언트 종료는 텍스트 통신을 위한 소켓에서 판단하기 때문에 음성을 전달하려고 하면 오류가 발생할 수 있다. 그래서 클라이언트들에게 broadcast하는 부분을 `try` 구문 안에 넣고, 만약 오류가 생겨 `except`에 걸린다면 클라이언트가 접속을 종료한 것으로 파악하고 접속 리스트에서 지운다.
```python=
def handle_client_voice(client):
	clients_voice[client] = 1
	while client in clients_voice:
		try:
			data = client.recv(1024)
			broadcast(data, dtype='voice')
		except Exception as _:
			client.close()
			del clients_voice[client]
```


## 4. Discussion
### 1. Trial and errors
* 놀랍게도 필요한 package를 사용하는데 파이썬 2, 3 버전문제를 미세하게 겪었다. 다양한 환경(ubuntu, window)에서 파이썬 버전관리를 하는 능력을 기르자.
* 텍스트 채팅과 음성 채팅을 각각 구현한 후 두 코드를 하나로 합치는 방식을 사용했다. 둘을 한 프로그램으로 합치자, 채팅이 서로 다른 포트를 사용하기 때문에 어느 텍스트 소켓과 어느 음성 소켓이 같은 클라이언트의 것인지를 구분하기가 어려워졌다. 메세지 자체는 모든 클라이언트에게 broadcast하기 때문에 상관이 없지만 접속 종료시 음성 소켓만 비정상적으로 종료된 채로 남아 오류가 발생하는 문제가 있었다. `try~except` 구문을 사용해서 소켓이 살아있는지를 보고, 그렇지 않으면 닫고 지우는 방법을 사용했다.
* 음성 전송을 처음 시도해봤을 때는 뚝뚝 끊어져서 수신자가 듣기 힘든 수준이었다. 음성이라는 아날로그 데이터를 연속적으로 전송하긴 쉽지 않기 때문에 chunk의 단위로 끊어서 전송하는데, chunk들 사이에 전송 지연이 발생하면서 수신자의 버퍼에는 underrun이 발생하고, 각 chunk들 사이를 무음으로 때워야 하기 때문에 음성이 끊기게 된다. 이 문제는 chunk 하나의 크기를 늘리면 해결되지만, 크기가 클 수록 latency가 커지기 때문에 적당한 선에서 타협을 봤다.
### 2. Additional improvements
* 코드가 environment dependent해서 지금 이 코드를 윈도우에서 실행시키면 정상적으로 동작하지 않는다. 그래서 윈도우 버전으로 같은 기능을 하는 프로그램을 시간이 된다면 작성해볼 수 있을 것이다.
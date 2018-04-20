# Simple text/voice/video chatting program
> CSED353 Computer Network Assignment 4
> 20160832 김근우
> 20160360 명성현
> 


## 1. Environment and Dependencies
이 프로그램은 Python 3.6, Window10 64비트 환경에서 제작했다. macOS 10.12에서 동작함을 확인했지만, 다른 환경에서는 의도한대로 작동하지 않을 수 있다. 클라이언트는 웹캠이 연결된 컴퓨터에서 실행해야 한다.


## 2. How to execute
프로그램은 ```client_full.py```와 ```server_full.py```로 구성되어 있다. 서버는 두 클라이언트 사이의 연결을 관리할 뿐, 실제로 채팅에 참여하지는 않는다.

``` bash!
> python3 server_full.py
Waiting for connection...
```
```bash!
> python3 client_full.py 127.0.0.1
```
![](https://github.com/k0nen/CSED353-Homeworks/blob/master/HW4/screenshot.png?raw=true)

클라이언트는 서버의 IP주소를 인자로 받는다. 올바른 주소를 입력했고 서버와 연결되면 GUI 창이 나타난다. 최초 입력창에는 대화명을 묻는 메세지가 적혀 있다. 사용할 닉네임을 적은 뒤 ```Send``` 버튼을 누르면 자유롭게 텍스트 채팅 기능을 사용할 수 있다.

## 3. Code
텍스트와 음성 채팅은 [이전 Assignment에서 구현한 코드](https://github.com/k0nen/CSED353-Homeworks/tree/master/HW3)를 사용했다. 이번 writeup에서는 영상 전송을 위한 부분만 설명한다.

### 1. Server
음성이나 텍스트와 마찬가지로, 서버는 내용이 어떤 형식인지는 궁금해하지 않아도 되고, 별도로 처리할 필요도 없다. `handle_client_video` 함수는 하나의 독립 스레드에서 돌아가며, 클라이언트에서 받은 영상 데이터를 다른 모든 클라이언트에게 뿌려주는 역할을 한다.
```python
def handle_client_video(client):
	clients_video[client] = 1
	while client in clients_video:
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
			chunk = client.recv(length - totrec)
			if chunk == '':
				raise RuntimeError("Socket connection broken")
			msgArray.append(chunk)
			totrec += len(chunk)

		broadcast(b''.join(metaArray + msgArray), dtype="video", sd=client)
```


### 2. Client

GUI 구현은 파이썬 기본 라이브러리에 내장된 `tkinter` 모듈을 사용했다. 영상은 영상을 출력하는 스레드들에서 출력할 것이고, 그 외에 실행 화면에 표시해야 할 요소인 스크롤바, 입력 필드, 전송 버튼, 개발자 정보, 채팅창은 아래와 같이 구현했다.

```python
scrollbar = tkinter.Scrollbar(messages_frame)

entry_field = tkinter.Entry(button_frame, textvariable=my_msg)
entry_field.bind("<Return>", send_text)
entry_field.pack(side=tkinter.LEFT, padx=10)

send_button = tkinter.Button(button_frame, text="Send", command=send_text)
send_button.pack(side=tkinter.LEFT, padx=10)

send_button = tkinter.Button(button_frame, text="Made by k0nen & gnu", command=send_text)
send_button.pack(side=tkinter.LEFT, padx=10)

msg_list = tkinter.Listbox(messages_frame, height=15, width=50, yscrollcommand=scrollbar.set)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
msg_list.pack(side=tkinter.TOP, fill=tkinter.BOTH)
```

영상 촬영을 위해 ```opencv-python``` 라이브러리를 사용했다. 카메라로부터 한 프레임을 가져오는 것은 이렇게 할 수 있다:
```python
import cv2
cap = cv2.VideoCapture(0)
ret_val, img = cap.read()
```
이제 ```img```에는 웹캠에서 가져온 프레임 하나가 들어있다. 이를 적당히 작은 용량을 가지도록 변환하고 메타데이터를 추가한 뒤, 서버로 전송하는 함수가 send_video이다.

```python
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
```

클라이언트의 화면에는 자신의 영상과 서버에서 받아온 다른 참석자의 영상을 같이 표시하는 방식을 택했다. 먼저 `show_my_video` 함수는 `send_video`와 동일하게 웹캠에서 한 프레임을 읽어온뒤 화면에 띄우는 역할을 한다.

```python
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
			panel.place(height=110, width=110, x=256, y=5)

		else:
			panel.configure(image=image)
			panel.image = image
```

`receive_video` 함수는 다른 참석자의 영상을 화면에 띄워주는 스레드이다. 
```python
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
```

## 4. Discussion
### 1. Trial and errors
* opencv를 이용하여 webcam의 frame을 가져와서 socket을 통해 send하는 과정에서 jpeg로 압축해야될 필요가 있었다. 하지만 frame을 jpeg로 바꿔주는 Pillow module에서 사용하는 rgb형식과 webcam에서 가져온 데이터가 사용하는 rgb형식이 달라서 이를 converting을 해줘야 했는데 처음에는 해주지 않아서 video가 색상반전이 생겼었다. 이는 opencv 내장 함수인 `cvtColor()`를 이용하여 해결할 수 있었다.
* python의 socket은 byte형태의 데이터만 send하고 recv할 수 있다. 하지만 frame을 처리할 때 사용되는 opencv api와 Pillow module의 함수들이 어떤 타입의 데이터를 return하는지 잘 알아보지 않고 사용하다 오류가 많이 생겼다. 이 때문에 각각의 api들에 대해 자세히 알아봐야 했고 꽤 애를 먹었다.
* 또한 python에서 byte형태의 데이터와 string형태의 데이터를 처리하는 함수가 달라서 이 또한 고려해줘야 했다.
* server 쪽에서 처음에는 broadcasting 방식을 통해 1:N 통신이 가능하도록 구현을 하려고 했었다. 하지만 voice chat에서 2개 이상의 socket에서 받은 voice를 1개에서 받은 것처럼 처리를 해줘야 했고 video같은 경우에는 2개이상의 socket에서 받은 frame을 구별해서 각각의 client들에게 보내주어야 했다. 또한 이를 받은 client는 어디서 온 frame인지 구별해서 screen에 띄워줘야 했다. 1:N은 poject의 요구사항도 아니었기 때문에 중간에 1:1 통신으로 디자인을 바꾸었다.
* frame의 resizing을 하더라도 기본적으로 1KB을 초과한다. 그래서 socket을 통해 보낼때 한번에 가지 않는 경우가 발생하는 그러면 client쪽에서는 손상된 frame을 받게 된다. 그래서 이 send를 reliable하게 만들어 주기 위해서 frame을 send할 때 frame의 크기에 대한 metadata를 head로 추가하여 send하였고 recv하는 쪽에서는 frame의 크기만큼 정확하게 recv를 할 수 있었다.
* GUI는 tkinter라는 python graphic module을 이용하였는데 window geometry때문에 처음에 애를 많이 먹었다.

### 2. Additional improvements
* 1:N chat을 가능하게 해주는 server를 구현해보고 싶다.
* 영상을 프레임 단위로 jpg 이미지로 변환해서 전송하는 방식을 선택했는데, 다른 압축 알고리즘이나 전송 방식을 사용했다면 더 높은 해상도나 framerate를 제공할 수 있을지도 모른다는 생각도 든다.
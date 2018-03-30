# Simple chatting program
> CSED353 Computer Network Assignment 2
> 20160832 김근우
> 20160360 명성현
> 
## 1. Environment and Requirements
This program was compiled using GCC 5.4.0 on Ubuntu 16.04 64bit operating system. The source code is written in C language.

## 2. How to execute
Although we prepared a precompiled server & client binary with the source codes, you can compile it on your own using the following commands:
```
gcc pthread -o server server.c
gcc pthread -o client client.c
```
When you run the server program, you will be asked to enter your name. This name will be shown in the client's screen. After setting a name, the server will prepare things required for communication and wait until a client connects.
```shell
ubuntu@ubuntu:~$ ./server
What is your name?
server_name
socket...
bind...
listen...
accept...
```
Now it's time to run the client program. You must provide the IP address of the server on command line. The client program will also ask for your name, which will be shown on the server's screen.
```shell
ubuntu@ubuntu:~$ ./client 127.0.0.1
What is your name?
my_client
```
If everything has been correctly configured, the client will establish a conection with the server, and both programs will clear its screen. From now on, the users can freely talk to each other. Pressing `Ctrl+C` from either side will quit both server and client. __A video demo has been submitted together.__


## 3. Code

### 1. Structure
```c=
struct packet {
  char user_name[NAME_LEN];
  char data[MAX_BUF];
}; 
```
The name which you entered is stored in this structure. Also when you send your chat data by socket you'll use this structure. This structure exists only one over the program. You'll reuse this structure object whenever sending the message.
### 2. Define
```c=
#define PORT 1025
#define MAX_PENDING 5
#define MAX_BUF 256
#define NAME_LEN 16
```
We used port number 1025 as 0 ~ 1024 is often used by other programs. MAX_PENDING is for `listen()` in server.c. MAX_BUF is the max length of message you can send. NAME_LEN is a max length of name you can use.
### 3. Global variables
__client.c__
```c=
int last_sent = 1; //This is for line feeding in chat form
int sock; //Store server's socket
char escape_string[] = "SIGINT"; //For recognizing the program is terminated
int escape_len = 6;

void (*old_sigint) (int); //Store the return value of `signal()`
void sigint_handler(int sig); //Signal handler for sigint(Ctrl + C)
```
__server.c__
```c=
int last_sent = 1;
int sock, client; //Server should store the sockets of both side.
char escape_string[] = "SIGINT";
int escape_len = 6;

void (*old_sigint) (int);
void sigint_handler(int sig);
```
Other things serve the same role with `client.c`
### 2. Function
__Common__
```c=
void *recv_message(void *client)
{ 
  int sock = *(int *)client;
  struct packet pack = { 0 };
  
  while(1)
  { 
    if(recv(sock, (void *)&pack, sizeof(struct packet), 0) == -1)
      perror("recv error:");
    else
    { 
      if(last_sent)
      { 
        printf("\n");
        last_sent = 0;
      }
      if (strcmp(escape_string, pack.data) == 0) {
        exit(0);
      }
      printf("%s: ", pack.user_name);
      printf("%s\n", pack.data);
    }
  }
}
```
This function is for thread which play a role in receiving the message. It receives the message as form of packet structure. It also feeds a line after checking if the program is right after the sending a message. And it checks whether the other side program is terminated by comparing the massage with esxape string we define as global variable.
```c=
void sigint_handler(int sig)
{
	struct packet pack = { 0 };
	strncpy(pack.data, escape_string, escape_len);
	pack.data[escape_len] = '\0';
	send(sock, (void *)&pack, sizeof(struct packet), 0);

        close(client); //Only in server.c
	close(sock);
	signal(SIGINT, old_sigint);
	exit(0);
}
```
This handler is for terminating the program correctly. We can terminate the program by send a sigint by push Ctrl + C. Then the handler is evoked and sends a escape_string to the other side program. After that, socket which was used by program are closed.

__client.c__
```c=
int main(int argc, char * argv[])
{
        ...
        
	/* Create a socket */
	puts("socket...");
	if ((sock = socket(PF_INET, SOCK_STREAM, 0)) == -1) 
        
        ...
	
	if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1)
        ...

	/* Create thread for recive message */
	p = pthread_create(&t, NULL, recv_message, &sock);
        
        ...

	system("clear");
	old_sigint = signal(SIGINT, sigint_handler);

	while(1)
	{
            ...
		send(sock, (void *)&pack, sizeof(struct packet), 0);
	}

        ...
}
```
In client progarm, It first makes endpoint of connection by call `socket()`. And we bring this return value, socket_fd, for connect to server. we can get the server's ip address by argv[1]. Now we are ready to communicate with server. To receive message independently from sending message, we create a thread only for receiving message and printing it to terminal. If the program get the Sigint then it is terminated.

__server.c__
```c=
int main()
{
        ...
        
	puts("socket...");
        
        ...
        
	if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &(int){ 1 }, sizeof(int)) < 0)
        
        ...
        
	if ((bind(sock, (struct sockaddr *)&addr, sizeof(addr))) == -1) 
      
        ...

	/* Listen for connections */
	puts("listen...");
	if(listen(sock, MAX_PENDING) == -1)
        
        ...

	/* Accept connections */
	puts("accept...");
	socklen_t len = sizeof(caddr);
	if ((client = accept(sock, (struct sockaddr *)&caddr, &len)) < 0) 
        
        ...

	/* Create thread for recive message */
	p = pthread_create(&t, NULL, recv_message, &client);
        
        ...

	system("clear");
	old_sigint = signal(SIGINT, sigint_handler);

	while(1)
	{
            ...
		send(client, (void *)&pack, sizeof(struct packet), 0);
	}

        ...
}
```
First the server program creates socket for communicating with client program. After binding the socket with early defined port, It wait for connection from client by `liste()`. If it percepts a connection then accepts the connection by `accept()` whoes return value is socket of client. The procedure of sending & receiving the message is same with client.

## 4. Discussion


Starting from the base program to our final version, we faced several issues. So we will discuss about what happened, and how we implemented the breakthroughs. First up, our earlier version of the project didn't support the same user sending conescutive messages. So we decided to use multi-threading to receive messages. In our final code, the thread running `recv_message` has a `while` loop that can receive consecutive messages without having to send a response to every message received.

Second, we didn't have a proper way to end the connection. If you kill either server or client process, the other one would run into infinite loop printing the last received message. To solve this problem, we need to properly close the socket when we exit one of the program. So we decided to implement a custom SIGINT handler.
```c=
void sigint_handler(int sig)
{
	struct packet pack = { 0 };
	strncpy(pack.data, escape_string, escape_len);
	pack.data[escape_len] = '\0';
	send(sock, (void *)&pack, sizeof(struct packet), 0);

	close(sock);
	exit(0);
}
```
When this handler is called, it sends the string `"SIGINT"` as it would send a normal message, and then close the socket. To handle this escape string, every received message is compared with the escape string.
```c=
if (strcmp(escape_string, pack.data) == 0) {
	exit(0);
}
```
If the string matches, it means the other side of the connection has got the `SIGINT` signal, therefore both programs will safely terminate.

The third issue was that when the server is closed prior to the client, the next attempt to run a server would run into a `bind()` error. It was because the socket that we were using wasn't closed properly, so the TCP protocol would set port we've been using in `TIME_WAIT` status. Therefore, the next attempt to use this port caused the `bind()` error. We've thought of two possible solutions for this. The initial idea was to use a different port every time we run a server, specified by the user by command line. But since using user-defined ports may have conflicts with the firewall, we moved on to a solution that can reuse the port. If we set the `SO_REUSEADDR` flag on the socket before binding, it will ignore the `TIME_WAIT` status and reuse the port anyway.
```c=
if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &(int){ 1 }, sizeof(int)) < 0)
{
    perror("setsockopt(SO_REUSEADDR) failed");
    exit(1);
}
```
Waiting for the `TIME_WAIT` period also works witout any code adjustments, but now we can close a server and restart the service instantly.

## 5. Additional Questions
1. After connecting with another program by `connect()` or `accept()`. The system buffer wasn't flushed when `printf()` is called in main thread. So we had to flush the buffer directly by `fflush()`. Why did this happen?

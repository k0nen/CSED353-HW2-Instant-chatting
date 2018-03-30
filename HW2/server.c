#include <stdio.h>
#include <sys/socket.h>
#include <stdlib.h>
#include <netinet/in.h>
#include <pthread.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>

#define PORT 1025
#define MAX_PENDING 5
#define MAX_BUF 256
#define NAME_LEN 16

int last_sent = 1;
int sock, client;
char escape_string[] = "SIGINT";
int escape_len = 6;

struct packet {
	char user_name[NAME_LEN];
	char data[MAX_BUF];
};

void (*old_sigint) (int);
void sigint_handler(int sig);

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

int main()
{
	struct sockaddr_in addr, caddr;
	char buf[MAX_BUF];
	int p, s_len, status;
	struct packet pack = { 0 };
	pthread_t t;

	puts("What is your name?");
	scanf("%20s", buf);
	strncpy(pack.user_name, buf, NAME_LEN);

	/* Create a socket */
	puts("socket...");
	if ((sock = socket(PF_INET, SOCK_STREAM, 0)) == -1) 
	{
		perror("socket error:");
		exit(1);
	}

	/* Bind to an endpoint */
  puts("bind...");
	memset((char *)&addr, 0, sizeof(addr));
	addr.sin_family = AF_INET;
	addr.sin_port = htons(PORT);
	addr.sin_addr.s_addr = htonl(INADDR_ANY);
	if (setsockopt(sock, SOL_SOCKET, SO_REUSEADDR, &(int){ 1 }, sizeof(int)) < 0)
	{
    perror("setsockopt(SO_REUSEADDR) failed");
    exit(1);
	}
	if ((bind(sock, (struct sockaddr *)&addr, sizeof(addr))) == -1) 
	{
		perror("bind error:");
		close(sock);
		exit(1);
	}

	/* Listen for connections */
	puts("listen...");
	if(listen(sock, MAX_PENDING) == -1)
	{
		perror("listen error:");
		exit(1);   
	}

	/* Accept connections */
	puts("accept...");
	socklen_t len = sizeof(caddr);
	if ((client = accept(sock, (struct sockaddr *)&caddr, &len)) < 0) 
	{
		perror("accept error:");
		exit(1);
	}

	/* Create thread for recive message */
	p = pthread_create(&t, NULL, recv_message, &client);
	if(p)
	{
		perror("thread_create error:");
		exit(1);
	}

	system("clear");
	old_sigint = signal(SIGINT, sigint_handler);

	while(1)
	{
		printf("You:");
				fflush(stdout);
		s_len = read(0, buf, MAX_BUF);

		strncpy(pack.data, buf, s_len);
		pack.data[s_len - 1] = '\0';
		send(client, (void *)&pack, sizeof(struct packet), 0);
		last_sent = 1;
	}

	close(client);
	close(sock);
	pthread_join(p, (void **)&status);
	return 0;
}

void sigint_handler(int sig)
{
	struct packet pack = { 0 };
	strncpy(pack.data, escape_string, escape_len);
	pack.data[escape_len] = '\0';
	send(client, (void *)&pack, sizeof(struct packet), 0);

	close(client);
	close(sock);
	exit(0);
}
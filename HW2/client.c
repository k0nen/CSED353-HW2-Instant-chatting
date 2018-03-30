#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <pthread.h>
#include <unistd.h>
#include <arpa/inet.h>
#include <signal.h>

#define PORT 1025
#define MAX_BUF 256
#define NAME_LEN 16

int last_sent = 1;
int sock;
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

int main(int argc, char * argv[])
{
	struct sockaddr_in server_addr;
	char *host;
	char buf[MAX_BUF];
	int s_len, p=0, status;
	struct packet pack = { 0 };
	pthread_t t;

	if (argc == 2) 
	{
		host = argv[1];
	}
	else 
	{
		puts("Usage: ./* [ip_address]\n");
		exit(1);
	}

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
	
	/* Connection */
	server_addr.sin_family = AF_INET;
	server_addr.sin_port = htons(PORT);
	server_addr.sin_addr.s_addr= inet_addr(host);
	if (connect(sock, (struct sockaddr *)&server_addr, sizeof(server_addr)) == -1)
	{
		perror("connect error");
		close(sock);
		exit(1);
	}

	/* Create thread for recive message */
	p = pthread_create(&t, NULL, recv_message, &sock);
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
		send(sock, (void *)&pack, sizeof(struct packet), 0);
		last_sent = 1;
	}

	close(sock);
	pthread_join(p, (void**)&status);
	return 0;
}

void sigint_handler(int sig)
{
	struct packet pack = { 0 };
	strncpy(pack.data, escape_string, escape_len);
	pack.data[escape_len] = '\0';
	send(sock, (void *)&pack, sizeof(struct packet), 0);

	close(sock);
	signal(SIGINT, old_sigint);
	exit(0);
}
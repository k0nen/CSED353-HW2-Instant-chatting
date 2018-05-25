/* 2018 CSED353 Assignment 6 - Part 3
	20160360 Sunghyun Myung
*/

#include <stdio.h>
#include <stdlib.h>
#include <pcap.h>
#include <string.h>
#include <malloc.h>
#include <arpa/inet.h>

char error_buffer[1000];

typedef struct __endhost {
	char *name;
	int packets;
	int bytes;
	struct __endhost *next;
} _endhost;

void update_endhost(const u_char *p, _endhost **head, int size) {
	char dst[16];
	_endhost *last, *ptr = *head;
	const u_char *pp = p + 16;
	inet_ntop(AF_INET, p + 16, dst, INET_ADDRSTRLEN);

	while(ptr != NULL) {
		if(strcmp(dst, ptr->name) == 0) {
			ptr->packets ++;
			ptr->bytes += size;
			return;
		}
		else {
			last = ptr;
			ptr = ptr->next;
		}
	}
	_endhost *newdata = (_endhost *)malloc(sizeof(_endhost));
	newdata->packets = 1;
	newdata->bytes = size;
	newdata->next = NULL;
	newdata->name = (char *)malloc(sizeof(char) * 16);
	strcpy(newdata->name, dst);
	if(*head == NULL) *head = newdata;
	else last->next = newdata;
}

void print_endhost(_endhost *head, FILE *fp) {
	_endhost *ptr = head;
	while(ptr != NULL) {
		fprintf(fp, "%s\t %d\t %d\t\n", ptr->name, ptr->packets, ptr->bytes);
		ptr = ptr->next;
	}
}

int main(int argc, char *argv[]) {
	// Data
	pcap_t *file;
	FILE *ep = NULL;

	// Misc
	const u_char *packet;
	struct pcap_pkthdr header;
	u_int16_t src_port, dest_port;

	// We are interested in the following:
	int total_packets = 0, total_bytes = 0;
	double timespan;
	int time_first, time_last;
	_endhost *hosts = NULL;
	int cnt_tcp = 0, cnt_udp = 0, cnt_icmp = 0;
	int cnt_ftp = 0, cnt_ssh = 0, cnt_dns = 0, cnt_http = 0;

	// Parse argument
	if(argc != 2 && argc != 3) {
		printf("Usage: ./program pcap_file endhost_output_file\n");
		printf("If endhost file isn't specified, there will be no endpoint analysis.\n");
		exit(1);
	}
	else {
		// Open .pcap file
		if((file = pcap_open_offline(argv[1], error_buffer)) == NULL) {
			printf("pcap_open_offline() failed.\n%s\n", error_buffer);
			exit(1);
		}
		if(argc == 3) {
			ep = fopen(argv[2], "w");
			if(ep == NULL) {
				printf("Failed to open \"%s\" for writing.\n", argv[2]);
				exit(1);
			}
		}
	}

	// Parse each packet
	while((packet = pcap_next(file, &header)) != NULL) {
		packet += 0x28;
		
		total_packets ++;
		total_bytes += header.len;

		// Record timestamp
		if(total_packets == 1) {
			time_first = header.ts.tv_sec * 1000000 + header.ts.tv_usec;
		}
		time_last = header.ts.tv_sec * 1000000 + header.ts.tv_usec;

		switch(*(packet + 0x17)) {
			case 0x01: cnt_icmp++; break;
			case 0x06: cnt_tcp++; break;
			case 0x11: cnt_udp++; break;
			default: break;
		}
 
 		src_port = *(packet + 0x22) * 256 + *(packet + 0x23);
 		dest_port = *(packet + 0x24) * 256 + *(packet + 0x25);
		if(src_port == 21 || dest_port == 21) cnt_ftp++;
		else if(src_port == 22 || dest_port == 22) cnt_ssh++;
		else if(src_port == 53 || dest_port == 53) cnt_dns++;
		else if(src_port == 80 || dest_port == 80) cnt_http++;

		update_endhost(packet + 0xe, &hosts, header.len);
	}

	// Print analysis results
	printf("Total packets: %d\n", total_packets);
	printf("Total bytes: %d\n\n", total_bytes);
	timespan = (double)(time_last - time_first);
	printf("Time difference between first/last packet: %.3fs\n", timespan / 1000000);

	printf("Packets per protocol\n");
	printf("TCP: %d, UDP: %d, ICMP: %d\n\n", cnt_tcp, cnt_udp, cnt_icmp);

	if(ep != NULL) {
		print_endhost(hosts, ep);
		printf("IP end host analysis written in \"%s\"\n", argv[2]);
		printf("In (IP address / # of packets / # of bytes order)\n");
		fclose(ep);
	}
	else {
		printf("End host analysis skipped\n");
		printf("To enable: run ./program pcap_file endhost_output_file\n\n");
	}

	printf("Packets per application\n");
	printf("FTP: %d, SSH: %d, DNS: %d, HTTP: %d\n\n", cnt_ftp, cnt_ssh, cnt_dns, cnt_http);

	printf("Average packet size: %dB\n", total_bytes / total_packets);
	printf("Average packet inter-arrival time: %.3fms\n", timespan / total_packets / 1000);
	return 0;
}

/* 2018 CSED353 Assignment 6 - Part 1
	20160360 Sunghyun Myung

	References:
	http://www.tcpdump.org/pcap.htm
	https://www.ibm.com/support/knowledgecenter/en/ssw_aix_61/com.ibm.aix.progcomc/libpcap_pcap2.htm
*/


#include <stdio.h>
#include <stdlib.h>
#include <pcap.h>
#include <time.h>

char error_buffer[1000];

int main(int argc, char *argv[]) {
	// We will grab packets from here
	char *device;
	pcap_t *link;

	// Capture timer
	clock_t start, finish;

	//Misc
	const u_char *packet;
	struct pcap_pkthdr header;
	struct bpf_program fp;
	char filter_exp[] = "(tcp or udp or icmp) and portrange 1-1024";
	bpf_u_int32 netp, maskp;
	int capture_period;

	// Dump packets to file
	pcap_dumper_t *dump_file;


	// arg check
	if(argc != 3) {
		printf("Usage: ./program time filename\n");
		printf("time: time to catch packets, in seconds\n");
		printf("filename: output file name\n");
		exit(0);
	}
	else {
		capture_period = atoi(argv[1]) * CLOCKS_PER_SEC;
	}

	// Find a device to capture packets from
	device = pcap_lookupdev(error_buffer);
	if(device == NULL) {
		printf("pcap_lookupdev() failed.\n%s\n", error_buffer);
		exit(1);
	}
	else {
		printf("Using device: %s\n", device);
		pcap_lookupnet(device, &netp, &maskp, error_buffer);
	}

	// Create a connection to device
	link = pcap_open_live(device, 2147483647, 0, -1, error_buffer);
	if(link == NULL) {
		printf("pcap_open_live() failed.\n%s\n", error_buffer);
		exit(1);
	}

	// Create filters to capture TCP, UDP, and ICMP only
	if(pcap_compile(link, &fp, filter_exp, 0, netp) == -1) {
		printf("pcap_compile() failed.\n%s\n", pcap_geterr(link));
		exit(1);
	}

	// Apply the created filter
	if(pcap_setfilter(link, &fp) == -1) {
		printf("pcap_setfilter() failed.\n%s\n", pcap_geterr(link));
		exit(1);
	}

	// Dump file
	if((dump_file = pcap_dump_open(link, argv[2])) == NULL) {
		printf("Error opening file \"%s\" for writing\n", argv[3]);
		printf("%s", pcap_geterr(link));
		exit(1);
	}

	start = clock();
	while(clock() < start + capture_period) {
		packet = pcap_next(link, &header);

		if(packet == NULL) {
			// Didn't get a packet yet
		}
		else {
			pcap_dump((u_char *)dump_file, &header, packet);
		}
	}

	pcap_dump_close(dump_file);
	pcap_close(link);

	return 0;
}
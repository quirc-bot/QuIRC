import socket
import time
import datetime
botnick = ''

def _parse_irc_packet(packet):
    irc_packet = _IRCPacket()
    irc_packet.parse(packet)
    return irc_packet

class _IRCPacket:
    def __init__(self):
        self.prefix = ""
        self.command = ""
        self.arguments = []

    def parse(self, packet):
        if packet.startswith(":"):
            self.prefix = packet[1:].split(" ")[0]
            packet = packet.split(" ", 1)[1]

        if " " in packet:
            if " :" in packet:
                last_argument = packet.split(" :")[1]
                packet = packet.split(" :")[0]
                for splitted in packet.split(" "):
                    if not self.command:
                        self.command = splitted
                    else:
                        self.arguments.append(splitted)
                self.arguments.append(last_argument)
            else:
                for splitted in packet.split(" "):
                    if not self.command:
                        self.command = splitted
                    else:
                        self.arguments.append(splitted)
        else:
            self.command = packet

class IRCConnection:
    def __init__(self):
        ##Creates a new IRC Connection. You need to call .connect on it to actually connect to a server.
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.nick = ""

        self.on_connect = []
        self.on_public_message = []
        self.on_private_message = []
        self.on_ping = []
        self.on_welcome = []
        self.on_packet_received = []
        self.on_join = []
        self.on_leave = []

    def run_once(self):
        ##This function runs one iteration of the IRC client. 
        #This is called in a loop by the run_loop function. 
        #It can be called separately, but most of the time there is no need to do this.
        
        packet = _parse_irc_packet(next(self.lines)) #Get next line from generator

        for event_handler in list(self.on_packet_received):
            event_handler(self, packet)

        if packet.command == "PRIVMSG":
            print('Message recieved')
            if packet.arguments[0].startswith("#"):
                print('Found channel message')
                for event_handler in list(self.on_public_message):
                    origin =  str(packet.arguments[0]) #channel
                    senduser = str(packet.prefix.split("!")[0]) #sender
                    content = packet.arguments[1].encode("ascii", "replace")
                    content = str(content) #message
                    print('Got message info')
                    logfile = open('bot.log', 'a+')
                    print('opened logs')
                    ts = time.time()
                    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    print('Got timestamp')
                    logline = '\n [' + origin + '] @ ' + st +' - ' + senduser + ' : ' + content
                    logline = str(logline)
                    logfile.write(logline)
                    print('Logged message')
                    print(logline)
                    logfile.close()
                    print('Closed logs file')
                    event_handler(self, packet.arguments[0], packet.prefix.split("!")[0], packet.arguments[1])
            else:
                for event_handler in list(self.on_private_message):
                    print('Found Private message')
                    senduser = str(packet.prefix.split("!")[0]) #sender
                    content = packet.arguments[1].encode("ascii", "replace")
                    content = str(content) #message
                    print('Got message info')
                    logfile = open('bot.log', 'a+')
                    print('Opened logs')
                    ts = time.time()
                    st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    print('Got timestamp')
                    logline = '\n [Private Message] @ ' + st +' - ' + senduser + ' : ' + content
                    logline = str(logline)
                    logfile.write(logline)
                    print('Logged message')
                    print(logline)
                    logfile.close()
                    print('Closed logs file')
                    event_handler(self, packet.prefix.split("!")[0], packet.arguments[1])
        elif packet.command == "PING":
            self.send_line("PONG :{}".format(packet.arguments[0]))
            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
            print('ping ponged server @ ' + st)
            for event_handler in list(self.on_ping):
                event_handler(self)
        elif packet.command == "433" or packet.command == "437":
            #Command 433 is "Nick in use"
            #Add underscore to the nick

            self.set_nick("{}_".format(self.nick))
            print('added _ to nick to 433 - nick in use')
        elif packet.command == "001":
            for event_handler in list(self.on_welcome):
                event_handler(self)
        elif packet.command == "JOIN":
            for event_handler in list(self.on_join):
                event_handler(self, packet.arguments[0], packet.prefix.split("!")[0])
        elif packet.command == "PART":
            for event_handler in list(self.on_leave):
                event_handler(self, packet.arguments[0], packet.prefix.split("!")[0])

    def run_loop(self):
        #Runs the main loop of the client. 
        #This function is usually called after you add all the callbacks and connect to the server.


        while True:
            self.run_once()

    def _read_lines(self):
        buff = ""
        while True:
            buff += self.socket.recv(1024).decode("utf-8", "replace")
            while "\n" in buff:
                line, buff = buff.split("\n", 1)
                line = line.replace("\r", "")
                yield line

    def connect(self, server, port=6667):
        #Connects to a given IRC server. 
        #After the connection is established, it calls the on_connect event handler.


        self.socket.connect((server, port))
        self.lines = self._read_lines()
        for event_handler in list(self.on_connect):
            event_handler(self)

    def send_line(self, line):
        #Sends a line directly to the server. 
        #This is a low-level function that can be used to implement functionality that's not covered by this library. 
        #Almost all of the time, you should have no need to use this function.


        self.socket.send("{}\r\n".format(line).encode("utf-8"))

    def send_message(self, to, message):
        #Sends a message to a user or a channel.
        global botnick
        print('Sending message...')
        print('message sent... logging..')
        logfile = open('bot.log', 'a+')
        print('Opened logs')
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print('Got timestamp')
        logline = '\n [' + to + '] @ ' + st +' -' + botnick + ' : ' + message
        logline = str(logline)
        logfile.write(logline)
        print('Logged message')
        print(logline)
        logfile.close()
        print('Closed logs')
        self.send_line("PRIVMSG {} :{}".format(to, message))
    def send_notice(self, to, message):
        global botnick
        #Sends a notice message. 
        #Notice messages ususally have special formatting on clients.


        print('Sending message...')
        print('message sent... logging..')
        logfile = open('bot.log', 'a+')
        print('Opened logs')
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print('Got timestamp')
        logline = '\n [' + to + '] @ ' + st +' -' + botnick + ' : ' + message
        logline = str(logline)
        logfile.write(logline)
        print('Logged message')
        print(logline)
        logfile.close()
        print('Closed logs')
        self.send_line("NOTICE {} :{}".format(to, message))
    def send_action_message(self, to, action):
        #Sends an action message to a channel or user. 
        #Action messages have special formatting on clients and are usually sent like /me is happy


        self.send_message(to, "\x01ACTION {}\x01".format(action))
        
    def join_channel(self, channel_name):
        #Joins a given channel. 
        #After the channel is joined, the on_join callback is called.


        self.send_line("JOIN {}".format(channel_name))
        print('Joined ' + channel_name)
    def set_nick(self, nick):
        #Sets or changes your link. 
        #This should be called before joining channels, but can be called at any time afterwards. 
        #If the requested nickname is not available, the library will keep adding an underscore until a suitable nick is found.
        global botnick
        print('setting nick')
        self.nick = nick
        self.send_line("NICK {}".format(nick))
        print('Nick: ' + nick)
        botnick = nick
        print('Opened Logs')
        
        logs = open('bot.log', 'a+')
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print('Got timestamp')
        logs.write('\n Nick was set to ' + nick + ' @ ' + st)
        print('Logged nickchange')
        logs.close()
        print('Closed logs')
        

    def send_user_packet(self, username):
        #Sends a user packet. This should be sent after your nickname. 
        #It is displayed on clients when they view your details and look at "Real Name".
        print('setting realname')
        self.send_line("USER {} 0 * :{}".format(username, username))
        print('Realname: ' + username)
        realname = username
        print('Opened Logs')
        
        logs = open('bot.log', 'a+')
        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print('Got timestamp')
        logs.write('\n Realname was set to ' + username + ' @ ' + st)
        print('Logged realname change')
        logs.close()
        print('Closed logs')
       

import imaplib
import email
import html2text
import ConfigParser
import os
import re
from pprint import pprint  

list_response_pattern = re.compile(r'\((?P<flags>.*?)\) "(?P<delimiter>.*)" (?P<name>.*)')

def open_connection(verbose=False):
    # Read the config file
    config = ConfigParser.ConfigParser()
    config.read([os.path.expanduser('~/dev/email/.mail_config.ini')])

    # Connect to the server
    hostname = config.get('Server', 'hostname')
    if verbose: print 'Connecting to', hostname
    connection = imaplib.IMAP4_SSL(hostname)

    # Login to account
    username = config.get('Account', 'username')
    password = config.get('Account', 'password')
    if verbose: print 'Logging in as', username
    connection.login(username, password)
    return connection

def parse_response(resp):
    # parse output for given server response and return each entity
    flags, delimiter, mailbox_name = list_response_pattern.match(resp).groups()
    mailbox_name = mailbox_name.strip('"')
    return(flags, delimiter, mailbox_name)

def list_mailboxes(open_connect):
    # print out list of available mailboxes
    typ, data = open_connect.list()
    pprint(data)

def list_mailboxes_by_pattern(open_connect, pattern):
    # list folders matching a pattern
    typ, data = open_connect.list(pattern=pattern)
    for line in data:
        print("Server Response: ", line)

def list_subfolders(open_connect, inbox):
    # print the list of subfolders in a given inbox
    typ, data = open_connect.list(directory=inbox)
    for line in data:
        print("Server Response: ", line)

def get_status(open_connect, inbox=""):
    # get status for all or a given folder
    if inbox == "":
        typ, data = open_connect.list()
    else:
        typ, data = open_connect.list(directory=inbox)

    for line in data:
        flags, delimiter, mailbox_name = parse_response(line)
        print (open_connect.status(mailbox_name, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)') )

def get_numMessages(open_connect, inbox):
    # return the number of messages in a given inbox
    typ, data = open_connect.select(inbox)
    num_msgs = int(data[0])
    return num_msgs

def get_email_header(open_connect, inbox, msg_id):
    # grab email header
    email_header = ''
    open_connect.select(inbox, readonly=True)
    typ, msg_data = open_connect.fetch(str(msg_id), '(RFC822)')
    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_string(response[1])
            for header in [ 'to', 'from', 'subject', 'date' ]:
                email_header += '%-8s: %s' %(header.upper(), msg[header]) + '\n'
    return  email_header

def get_email_body(open_connect, inbox, msg_id):
    # grab email
    email_message = ''
    open_connect.select(inbox, readonly=True)
    typ, msg_data = open_connect.fetch(str(msg_id), '(RFC822)')
    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_string(response[1])
            for line in email.iterators.body_line_iterator(msg):
                email_string = html2text.html2text(line)
                email_message += email_string
    return (email_message)





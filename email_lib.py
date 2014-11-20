import imaplib
import email
import html2text
import ConfigParser
import os
from pprint import pprint  

def open_connection(verbose=False):
    ''' Establish imap SSL connection to inbox '''

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

def list_mailboxes(open_connect):
    ''' Print out list of available mailboxes '''
    
    typ, data = open_connect.list()
    pprint(data)

def list_mailboxes_by_pattern(open_connect, pattern):
    ''' List folders matching a pattern '''
    
    typ, data = open_connect.list(pattern=pattern)
    for line in data:
        print("Server Response: ", line)

def list_subfolders(open_connect, inbox):
    ''' Print the list of subfolders in a given inbox '''
    
    typ, data = open_connect.list(directory=inbox)
    for line in data:
        print("Server Response: ", line)

def list_email_parts(open_connect, inbox, msg_id):
    ''' Display different parts of the email '''
    
    open_connect.select(inbox, readonly=True)
    result,data = open_connect.fetch(msg_id, '(RFC822)')
    raw_email = data[0][1]
    email_message = email.message_from_string(raw_email)
    for part in email_message.items():
        print part

def get_status(open_connect, inbox=""):
    '''Get status for all or a given folder '''
    
    if inbox == "":
        typ, data = open_connect.list()
    else:
        typ, data = open_connect.list(directory=inbox)

    for line in data:
        flags, delimiter, mailbox_name = parse_response(line)
        print (open_connect.status(mailbox_name, '(MESSAGES RECENT UIDNEXT UIDVALIDITY UNSEEN)') )

def get_numMessages(open_connect, inbox):
    ''' return the number of messages in a given inbox'''

    typ, data = open_connect.select(inbox)
    num_msgs = int(data[0])
    return num_msgs

def get_date(open_connect, inbox, msg_id):
    ''' grab the date field of the email header'''
    
    open_connect.select(inbox, readonly=True)
    typ, msg_data = open_connect.fetch(msg_id, '(RFC822)')
    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_string(response[1])
            for header in ['date']:
                date_header = msg[header]
    
    return date_header

def get_subject(open_connect, inbox, msg_id):
    ''' grab the subject field of the email header '''
    
    typ, msg_data = open_connect.fetch(msg_id, '(RFC822)')
    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_string(response[1])
            for header in ['subject']:
                subject_header = msg[header]

    return subject_header

def get_email_header(open_connect, inbox, msg_id):
    ''' If you just want the header '''

    email_header = ''
    open_connect.select(inbox, readonly=True)
    typ, msg_data = open_connect.fetch(str(msg_id), '(RFC822)')
    for response in msg_data:
        if isinstance(response, tuple):
            msg = email.message_from_string(response[1])
            for header in [ 'to', 'from', 'subject', 'date' ]:
                email_header += '%-8s: %s' %(header.upper(), msg[header]) + '\n'
    return  email_header

def get_decoded_email_body(message_body):
    """ Decode utf-8 encoding """
    
    msg = email.message_from_string(message_body)
    text = ""
    html = None

    # Check to see if email is multipart
    if msg.is_multipart():
        
        for part in msg.get_payload():
            charset = part.get_content_charset()
 
            # Decode utf-8 for text and html 
            if part.get_content_type() == 'text/plain':
                text = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')
            if part.get_content_type() == 'text/html':
                html = unicode(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')
 
        if text is not None:
            return text
        else:
            return html2text.html2text(html)
    else:
        text = unicode(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text

def get_email_by_msgID(open_connect, inbox, msg_id):
    ''' Get email by msgID '''
    
    email_header=''
    open_connect.select(inbox, readonly=True)
    result,data = open_connect.fetch(msg_id, '(RFC822)')
    raw_email = data[0][1]
    email_message = email.message_from_string(raw_email)
    
    # Grab the email header info
    for header in [ 'to', 'from', 'subject', 'date' ]:
        email_header += '%-8s: %s' %(header.upper(), email_message[header]) + '\n'

    # Now get body
    for part in email_message.get_payload():
        charset = email_message.get_content_charset()
        
        # check for utf-8 encoding
        if str(charset) == "utf-8":
            email_body = get_decoded_email_body(raw_email)
            return str(email_header) + str(email_body)

    # Check to see if email is multipart (has multiple parts)
    email_body = ''
    
    if email_message.is_multipart():
        for part in email_message.get_payload():
            if part.get_content_maintype() == "text":
                email_body = part.get_payload()
    else:
        email_body = email_message.get_payload()

    return str(email_header) + (email_body)


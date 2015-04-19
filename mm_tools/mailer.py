# -*- coding: utf-8 -*-

from gevent import monkey
monkey.patch_all()

import logging
import smtplib
import socket

from gevent import pool

try:
    GLOBAL_DEFAULT_TIMEOUT = socket._GLOBAL_DEFAULT_TIMEOUT
except:
    GLOBAL_DEFAULT_TIMEOUT = None
    
class SMTP(smtplib.SMTP):
    
    def __init__(self, host='', port=0, 
                 local_hostname=None, 
                 timeout=GLOBAL_DEFAULT_TIMEOUT,
                 source_ip=None):
        
        smtplib.SMTP.__init__(self, host=host, port=port, local_hostname=local_hostname, timeout=timeout)
        
        self._source_ip = source_ip
            
    def _get_socket(self, port, host, timeout):
        if self.debuglevel > 0:
            print 'connect:', (host, port)
        #socket.create_connection(address[, timeout[, source_address]]) :
        if self._source_ip: 
            source_address = (self._source_ip, 0)
            return socket.create_connection((port, host), timeout, source_address=source_address)
        else:
            return socket.create_connection((port, host), timeout)            

    def xclient(self, addr=None, name=None, helo=None, proto='ESMTP'):
        """Postfix XCLIENT extension
        
        http://www.postfix.org/XCLIENT_README.html
        
        required: smtpd_authorized_xclient_hosts
        
        PROTO SMTP or ESMTP
        
        attribute-name = ( NAME | ADDR | PORT | PROTO | HELO | LOGIN (SASL) )  
        
        ADDR UNAVAILABLE ?
        """
        xclient_cmd = 'XCLIENT NAME=%s ADDR=%s PROTO=%s HELO=%s' % (name or addr,
                                                                    addr,
                                                                    proto,
                                                                    helo or name or addr)
        
        (code,msg) = self.docmd(xclient_cmd)
        return (code,msg)

    def xforward(self, addr=None, name=None, helo=None):
        u"""Postfix XFORWARD extension
        
        http://www.postfix.org/XFORWARD_README.html
        
        required: smtpd_authorized_xforward_hosts
        
        """
        xforward_cmd = 'XFORWARD NAME=%s ADDR=%s HELO=%s' % (name or addr, 
                                                             addr, 
                                                             helo or name or addr)
        (code,msg) = self.docmd(xforward_cmd)
        return (code,msg)

class SMTPClient(object):
    
    def __init__(self, 
                 host='127.0.0.1', 
                 port=25,
                 source_ip=None, 
                 xclient_enable=False,
                 xforward_enable=False,
                 timeout=GLOBAL_DEFAULT_TIMEOUT,
                 tls=False, 
                 login=False, username=None, password=None,
                 debug_level=0):
        
        self.host = host
        self.port = port
        self.source_ip = source_ip
        self.timeout = timeout
        
        if xclient_enable and xforward_enable:
            raise ValueError("Please choice xclient or xforward protocol")
        
        self.xclient_enable = xclient_enable
        self.xforward_enable = xforward_enable
        self.tls = tls
        self.login = login
        self.username = username
        self.password = password or ''        
        self.debug_level = debug_level
        
    def send_multi(self, messages):
        results = {}
        for message in messages:
            results[message['id']] = self.send(message)
        return results

    def send_multi_parallel(self, pool_size=10, messages=[]):
        greenlets = []
        _pool = pool.Pool(pool_size)        
        
        for message in messages:
            greenlets.append(_pool.spawn(self.send, message))        
        
        _pool.join()

        results = {}
        for g in greenlets:
            message = g.value
            results[message['id']] = message
        
        return results
        
    def send(self, message):
        
        result = { 'success': False, 'id': message['id']}
        try:
            smtp_client = SMTP(source_ip=self.source_ip, timeout=self.timeout)
            smtp_client.set_debuglevel(self.debug_level)

            (code, msg) = smtp_client.connect(self.host, self.port)
            result['CONNECT'] = (code, msg)
                        
            if self.tls:
                (code, msg) = smtp_client.starttls()#keyfile, certfile
                result['TLS'] = (code, msg)
                print "tls : ", code, msg
                
            if self.login:
                (code, msg) = smtp_client.login(self.username, self.password)
                result['LOGIN'] = (code, msg)
                print "login : ", code, msg            
            
            (code, msg) = smtp_client.ehlo("helo.example.net")
            result['EHLO'] = (code, msg)

            features = smtp_client.esmtp_features
            if self.xclient_enable and "xclient" in features:
                (code, msg) = smtp_client.xclient(addr=message.get('from_ip'), 
                                                  name=message.get('from_hostname', None), 
                                                  helo=message.get('from_heloname', None))
                
                result['XCLIENT'] = (code, msg)
                
            elif self.xforward_enable and "xforward" in features:
                (code, msg) = smtp_client.xforward(addr=message.get('from_ip'), 
                                                   name=message.get('from_hostname', None), 
                                                   helo=message.get('from_heloname', None))
                result['XFORWARD'] = (code, msg)

            #'<send@toto.fr>'
            (code, msg) = smtp_client.mail(smtplib.quoteaddr(message['from']))
            result['MAIL FROM'] = (code, msg)
            
            for recipient in message['tos']:
                (code, msg) = smtp_client.rcpt(smtplib.quoteaddr(recipient))
                result['RCPT TO[%s]' % recipient] = (code, msg)
                
            #data + message
            (code, msg) = smtp_client.data(message['message'])
            result['DATA'] = (code, msg)
                
            (code, msg) = smtp_client.quit()
            result['QUIT'] = (code, msg)
            
            result['success'] = True
            
        except Exception, err:
            result['EXCEPTION'] = str(err)

        return result

class GmailSMTPClient(SMTPClient):
    """
    TODO: vérifier param et exception si non compatible
    
    TODO: voir limitation gmail selon mode choisi : https://support.google.com/a/answer/176600?hl=fr
    
    """
    def __init__(self, 
                 host='smtp.gmail.com', 
                 port=587, 
                 tls=True, 
                 login=True, username=None, password=None, 
                 **kwargs):
        SMTPClient.__init__(self, host=host, port=port, source_ip=source_ip, xclient_enable=xclient_enable, xforward_enable=xforward_enable, timeout=timeout, tls=tls, login=login, username=username, password=password, debug_level=debug_level)    

def main():    
    from pprint import pprint as pp
    from .message import MessageFaker
    
    '''Simple message for gmail'''
    """
    gmail_client = SMTPClient(host='smtp.gmail.com', 
                              port=587, timeout=5.0, debug_level=1,
                              login=True, tls=True, username="xxxx",
                              password="xxx")
    
    msg1 = MessageFaker(enveloppe_sender="xxx", 
                        enveloppe_recipients=["xxx"]).create_message()
    result = gmail_client.send(msg1)
    pp(result)
    """
    
    
    client = SMTPClient(port=14001, xforward_enable=True, timeout=5.0, debug_level=0)
    
    '''Simple message'''
    msg1 = MessageFaker().create_message()
    result = client.send(msg1)
    pp(result)
    
    return
    
    '''Multi Message sync'''
    result = client.send_multi([MessageFaker().create_message(), MessageFaker().create_message()])
    pp(result)
    
    '''Multi Message Parallel'''
    result = client.send_multi_parallel(messages=[MessageFaker().create_message(), MessageFaker().create_message()])
    pp(result)
    
        
if __name__ == "__main__":
    """
    python -m mongo_mail_server --server debug --host 127.0.0.1 --port 14001 start
    python -m mm_tools.mailer
    """    
    main()
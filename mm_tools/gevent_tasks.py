# -*- coding: utf-8 -*-

import logging
import gevent
import random

class GeventTimer(object):
    """
    Usage:
    
    >>> def mycall(): pass
    >>> timer = GeventTimer(mycall, 5.0)
    >>> gevent.spawn(timer.run)
    """
    
    def __init__(self, callback, callback_kwargs={}, sleep=60.0, random_sleep=False, stop_with_error=False, logger=None):
        
        if not callable(callback):
            raise ValueError("callback method is not callable")
        
        self.callback = callback
        self.callback_kwargs = callback_kwargs or {}
        self._running = False
        self._sleep = sleep
        self._random_sleep = random_sleep
        self.stop_with_error = stop_with_error
        self.logger = logger or logging.getLogger(__name__)
    
    def run(self):
        self._running = True
        
        self.logger.info('Timer running...')
        
        while self._running is True:
            if self._random_sleep:
                _sleep = random.randint(1.0, self._sleep)
            else:
                _sleep = self._sleep
            gevent.sleep(_sleep)
            try:
                self.logger.debug("run tasks...")
                self.callback(**self.callback_kwargs)
            except Exception, err:
                self.logger.error(str(err))
                if self.stop_with_error:
                    raise
                
            gevent.sleep()
        
        self.logger.info('Timer stopping...')
            
    def stop(self):
        self._running = False


def sent_fake_mail_task(host='127.0.0.1', port=25, 
                        xforward_enable=True,
                        period=30.0,
                        message_per_step=2,
                        vary_message_type=True,
                        random_files=1,
                        smtp_timeout=10,
                        stop_with_error=False,
                        domains=[], mynetworks=[]):
    from .mailer import SMTPClient
    from .message import MessageFaker
    
    client = SMTPClient(host=host, 
                        port=port, 
                        timeout=smtp_timeout,
                        xforward_enable=xforward_enable)
    
    def task(client=None, random_files=0, vary_message_type=True, message_per_step=1, domains=[], mynetworks=[]):
        kwarg_multipart = {'random_files': random_files}
        kwarg_singlepart = {}
        
        for i in xrange(0, message_per_step):
            if vary_message_type:
                kwargs = random.choice([kwarg_multipart, kwarg_singlepart])
            else:
                kwargs = kwarg_singlepart
            msg = MessageFaker(domains=domains, mynetworks=mynetworks, **kwargs).create_message()
            result = client.send(msg)
    
    callback_kwargs = dict(client=client, 
                           message_per_step=message_per_step,
                           random_files=random_files, 
                           vary_message_type=vary_message_type,
                           domains=domains, mynetworks=mynetworks)
    
    timer = GeventTimer(callback=task, callback_kwargs=callback_kwargs, 
                        sleep=period, random_sleep=True, 
                        stop_with_error=stop_with_error)
    try:
        timer.run()
    except KeyboardInterrupt:
        pass

def main():
    logging.basicConfig(level=logging.DEBUG)
    sent_fake_mail_task(period=5, port=14001, stop_with_error=True)

if __name__ == "__main__":
    """
    python -m mm_tools.gevent_tasks
    """
    main()



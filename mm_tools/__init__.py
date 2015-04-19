__VERSION__ = "0.1.0"

try:
    from gevent import monkey
    monkey.patch_all()
except:
    pass    

import os

try:
    global_vhost = os.environ['POSTAGE_VHOST']
except KeyError:
    global_vhost = '/'

try:
    global_user = os.environ['POSTAGE_USER']
except KeyError:
    global_user = 'guest'

try:
    global_password = os.environ['POSTAGE_PASSWORD']
except KeyError:
    global_password = 'guest'

if 'POSTAGE_DEBUG_MODE' in os.environ and os.environ['POSTAGE_DEBUG_MODE'].lower() == 'true':
    debug_mode = True
else:
    debug_mode = False

# This is the default HUP (Host, User, Password)
global_hup = {
    'host': 'localhost',
    'user': global_user,
    'password': global_password
}

# Just a simple log to remember the virtual host we are using
if debug_mode:
    print("postage.messaging: global_vhost set to {0}".format(global_vhost))

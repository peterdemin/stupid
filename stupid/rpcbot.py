import copy
import logging
import threading
from xmlrpc.server import SimpleXMLRPCServer

from stupid.chatbot import ChatBot


logger = logging.getLogger('stupid.rpc')


class RPCBot(ChatBot):

    def __init__(self, *args, **kwargs):
        super(RPCBot, self).__init__(*args, **kwargs)
        self.lock = threading.RLock()
        with self.lock:
            self._pending_messages = []
        self.start_rpc_server()

    def run_pending(self):
        with self.lock:
            messages = copy.deepcopy(self._pending_messages)
            self._pending_messages.clear()
        for message in messages:
            channel_id = self.broker.channel_id(message['channel'])
            self.broker.post(
                message['text'],
                channel_id=channel_id,
            )

    def post(self, message):
        with self.lock:
            self._pending_messages.append(message)

    def start_rpc_server(self):
        def post_handler(channel, text):
            self.post({
                'channel': channel,
                'text': text,
            })
            return True
        self.server = SimpleXMLRPCServer(("localhost", 34278))
        self.server.register_introspection_functions()
        self.server.register_function(post_handler, 'post')
        self.rpc_thread = threading.Thread(target=self.server.serve_forever)
        self.rpc_thread.daemon = True
        self.rpc_thread.start()

import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Add parent directory to path to import server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Add generated to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'generated'))

import server
# We need to mock chat_pb2 before importing server if it was doing top-level imports that fail,
# but server.py does dynamic imports inside serve() or uses sys.path. 
# Actually server.py imports xai_sdk at top level.

# We need to mock chat_pb2.ChatResponse because server.py uses it.
# But server.py imports it inside serve() or we need to make sure it's available.
# Wait, server.py has `import chat_pb2` inside `serve`? 
# No, I put `sys.path.append` then `import chat_pb2` commented out?
# Let's check server.py content again.

# In server.py:
# sys.path.append(os.path.join(os.path.dirname(__file__), 'generated'))
# ...
# yield chat_pb2.ChatResponse(chunk=content)

# So `chat_pb2` must be imported. 
# I should fix server.py to import chat_pb2 at top level after sys.path hack.
# Or I can mock it in the test.

# Let's assume chat_pb2 is available because we ran protoc.

import chat_pb2

class TestChatService(unittest.IsolatedAsyncioTestCase):
    async def test_stream_chat(self):
        # Mock request
        request = MagicMock()
        request.messages = [MagicMock(role='user', content='hello')]
        context = MagicMock()

        # Mock xAI Client
        with patch('xai_sdk.Client') as MockClient:
            mock_client_instance = MockClient.return_value
            mock_sampler = MagicMock()
            mock_client_instance.sampler = mock_sampler
            
            # Mock sample method to return an async iterator
            async def async_gen():
                # Yield objects that behave like tokens
                t1 = MagicMock()
                t1.token_str = "Hello"
                yield t1
                
                t2 = MagicMock()
                t2.token_str = " World"
                yield t2
            
            mock_sampler.sample.return_value = async_gen()

            service = server.ChatServiceServicer()
            service.client = mock_client_instance # Inject mock

            responses = []
            async for resp in service.StreamChat(request, context):
                responses.append(resp.chunk)

            self.assertEqual(responses, ["Hello", " World"])

if __name__ == '__main__':
    unittest.main()

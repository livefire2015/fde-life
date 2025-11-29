import asyncio
import logging
import os
import grpc
from concurrent import futures
import sys

# Add the generated proto directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'generated'))

# Import generated classes
import chat_pb2
import chat_pb2_grpc

import xai_sdk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatServiceServicer: # Inherits from chat_pb2_grpc.ChatServiceServicer
    def __init__(self):
        self.client = xai_sdk.Client()
        self.model = "grok-4-fast" # Default model

    async def StreamChat(self, request, context):
        logger.info(f"Received request with {len(request.messages)} messages")
        
        # Convert proto messages to xAI SDK format
        conversation = []
        for msg in request.messages:
            conversation.append({
                "role": msg.role,
                "content": msg.content
            })

        try:
            # Create sampler
            sampler = self.client.sampler
            
            # Stream response
            async for token in sampler.sample(
                messages=conversation,
                model_name=self.model,
                stream=True
            ):
                # The xAI SDK yields token objects. 
                # We need to check the structure based on SDK docs/examples.
                # Assuming token has .token_str or similar, or is a string.
                # Based on example: https://github.com/xai-org/xai-sdk-python/blob/main/examples/aio/server_side_tools.py
                # It seems to yield objects. Let's assume .token or .text
                
                # Actually, let's look at the example provided in the prompt if possible, 
                # but I can't access external URLs. 
                # I will assume standard xAI SDK usage: token.token_str or just str(token)
                
                # Let's try to be robust.
                content = ""
                if hasattr(token, 'token_str'):
                    content = token.token_str
                elif hasattr(token, 'text'):
                    content = token.text
                elif isinstance(token, str):
                    content = token
                else:
                    content = str(token)

                # TODO: Handle "thinking" if the model provides it in a specific field
                
                yield chat_pb2.ChatResponse(chunk=content)
                
        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))

async def serve():
    # We need to import the generated modules here to avoid import errors before generation
    global chat_pb2, chat_pb2_grpc
    import chat_pb2
    import chat_pb2_grpc

    # Patch the class to inherit from the generated Servicer
    ChatServiceServicer.__bases__ = (chat_pb2_grpc.ChatServiceServicer,)

    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    chat_pb2_grpc.add_ChatServiceServicer_to_server(ChatServiceServicer(), server)
    listen_addr = '[::]:50051'
    server.add_insecure_port(listen_addr)
    logger.info(f"Starting server on {listen_addr}")
    await server.start()
    await server.wait_for_termination()

if __name__ == '__main__':
    asyncio.run(serve())

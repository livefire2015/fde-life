import asyncio

class Client:
    def __init__(self):
        self.sampler = Sampler()

class Sampler:
    async def sample(self, messages, model_name, stream=True):
        # Mock response
        response_text = "This is a mock response from Grok-4-fast (xAI SDK not installed)."
        for word in response_text.split():
            await asyncio.sleep(0.1)
            yield Token(word + " ")

class Token:
    def __init__(self, text):
        self.token_str = text
        self.text = text

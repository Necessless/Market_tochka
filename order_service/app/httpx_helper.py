import httpx

class Httpx_Helper:
    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout
    
    async def client_getter(self):
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            yield client
    
    
httpx_helper = Httpx_Helper()
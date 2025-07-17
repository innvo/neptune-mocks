#!/usr/bin/env python3

import asyncio
import aiohttp
import ssl
import logging

async def test_localhost_connection():
    """Test the SSL fix for localhost connections"""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test URL (localhost:8182)
    url = "https://localhost:8182/status"
    
    # Create SSL context that disables hostname verification for localhost
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    logger.info("Testing localhost connection with SSL fix...")
    
    connector = aiohttp.TCPConnector(ssl=ssl_context)
    
    try:
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    logger.info("✓ Successfully connected to localhost:8182")
                    return True
                else:
                    logger.error(f"✗ Connection failed with status: {response.status}")
                    return False
    except ssl.SSLCertVerificationError as e:
        logger.error(f"✗ SSL certificate verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Connection test failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_localhost_connection())
    if result:
        print("SSL fix test PASSED")
    else:
        print("SSL fix test FAILED") 
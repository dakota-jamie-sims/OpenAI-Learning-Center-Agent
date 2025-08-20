import asyncio
import aiohttp
from typing import List, Tuple, Dict
from datetime import datetime

async def _check_one(session: aiohttp.ClientSession, url: str) -> Dict[str, any]:
    """Check a single URL and return detailed status information."""
    result = {
        'url': url,
        'status': 0,
        'error': None,
        'checked_at': datetime.now().isoformat(),
        'response_time': None
    }
    
    try:
        start_time = asyncio.get_event_loop().time()
        
        # Try HEAD request first (faster)
        async with session.head(url, allow_redirects=True, timeout=15) as resp:
            result['response_time'] = asyncio.get_event_loop().time() - start_time
            
            if resp.status >= 400:
                # If HEAD fails, try GET (some servers don't support HEAD)
                async with session.get(url, allow_redirects=True, timeout=20) as resp2:
                    result['status'] = resp2.status
                    result['response_time'] = asyncio.get_event_loop().time() - start_time
            else:
                result['status'] = resp.status
                
    except asyncio.TimeoutError:
        result['error'] = 'Timeout'
    except aiohttp.ClientError as e:
        result['error'] = f'Client error: {str(e)}'
    except Exception as e:
        result['error'] = f'Unexpected error: {str(e)}'
    
    return result

async def check_urls(urls: List[str]) -> List[Dict[str, any]]:
    """Check multiple URLs concurrently and return detailed results."""
    timeout = aiohttp.ClientTimeout(total=30)
    connector = aiohttp.TCPConnector(limit=10)  # Limit concurrent connections
    
    async with aiohttp.ClientSession(
        timeout=timeout,
        connector=connector,
        headers={'User-Agent': 'Dakota-Link-Checker/1.0'}
    ) as session:
        tasks = [_check_one(session, u) for u in urls]
        return await asyncio.gather(*tasks)

def get_url_verification_summary(results: List[Dict[str, any]]) -> Dict[str, any]:
    """Generate a summary of URL verification results."""
    total = len(results)
    successful = sum(1 for r in results if r['status'] == 200)
    failed = [r for r in results if r['status'] != 200]
    
    return {
        'total_checked': total,
        'successful': successful,
        'failed': len(failed),
        'all_valid': successful == total,
        'failed_urls': failed,
        'summary': f"{successful}/{total} URLs returned 200 status"
    }

## RAZA PY ###

import argparse
import asyncio
import logging
import random
import os
import sys
from itertools import count
from urllib.parse import unquote
from playwright.async_api import async_playwright

# Terminal colors for better visibility
COLORS = {
    'red': '\033[1;31m',
    'green': '\033[1;32m',
    'yellow': '\033[1;33m',
    'cyan': '\033[36m',
    'blue': '\033[1;34m',
    'reset': '\033[0m',
    'magenta': '\033[1;35m',
    'white': '\033[1;37m'
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('instagram_gc_renamer.log'),
        logging.StreamHandler()
    ]
)

# Anti-detection script
async def apply_anti_detection(page):
    await page.evaluate("""() => {
        Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
        window.chrome = { app: {}, runtime: {} };
    }""")

# Global counters and locks
name_counter = count(1)
used_names = set()
success_count = 0
fail_count = 0
stats_lock = asyncio.Lock()

# Invisible characters for bypass
INVISIBLE_CHARS = ["\u200B", "\u200C", "\u200D", "\u2060"]

def generate_name(base_names, use_invisible=True):
    """Generate unique names with invisible characters"""
    while True:
        base = random.choice(base_names)
        
        if use_invisible:
            # Add 1-3 random invisible chars
            num_invis = random.randint(1, 3)
            invis_text = "".join(random.choice(INVISIBLE_CHARS) for _ in range(num_invis))
            pos = random.choice([0, len(base)//2, len(base)])
            name = base[:pos] + invis_text + base[pos:]
        else:
            name = base
        
        # Add counter for uniqueness
        suffix = next(name_counter)
        final_name = f"{name}_{suffix}"
        
        if final_name not in used_names:
            used_names.add(final_name)
            return final_name

async def ultra_fast_rename(page, new_name):
    """Ultra-fast rename using direct JavaScript execution"""
    try:
        result = await page.evaluate("""(newName) => {
            return new Promise((resolve) => {
                // Find and click change button
                const changeBtn = Array.from(document.querySelectorAll("div[role='button']"))
                    .find(el => el.getAttribute('aria-label') === 'Change group name');
                
                if (!changeBtn) {
                    resolve({success: false, error: 'Change button not found'});
                    return;
                }
                
                changeBtn.click();
                
                setTimeout(() => {
                    // Find input field
                    const input = document.querySelector("input[aria-label='Group name']");
                    if (!input) {
                        resolve({success: false, error: 'Input field not found'});
                        return;
                    }
                    
                    // Clear and set new value
                    input.value = '';
                    input.focus();
                    input.value = newName;
                    
                    // Trigger input event
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Find save button
                    const saveBtn = Array.from(document.querySelectorAll("div[role='button']"))
                        .find(el => el.textContent.includes('Save'));
                    
                    if (saveBtn && saveBtn.getAttribute('aria-disabled') !== 'true') {
                        saveBtn.click();
                        resolve({success: true});
                    } else {
                        resolve({success: false, error: 'Save button not available'});
                    }
                }, 100);
            });
        }""", new_name)
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

async def rename_worker(context, thread_url, base_names, worker_id):
    """Worker task for parallel renaming"""
    global success_count, fail_count
    
    page = await context.new_page()
    await apply_anti_detection(page)
    
    try:
        # Navigate to thread
        await page.goto(thread_url, wait_until='domcontentloaded', timeout=60000)
        
        # Open details pane
        details_btn = page.locator("div[role='button'][aria-label='Open the details pane of the chat']")
        await details_btn.wait_for(timeout=30000)
        await details_btn.click()
        
        # Wait for change button
        change_btn = page.locator("div[role='button'][aria-label='Change group name']")
        await change_btn.wait_for(timeout=30000)
        
        logging.info(f"🚀 Worker {worker_id} ready for renaming")
        
        # Continuous renaming loop
        while True:
            name = generate_name(base_names)
            
            result = await ultra_fast_rename(page, name)
            
            async with stats_lock:
                if result['success']:
                    success_count += 1
                    logging.info(f"✅ Worker {worker_id} renamed to: {name}")
                else:
                    fail_count += 1
                    logging.warning(f"❌ Worker {worker_id} failed: {result.get('error', 'Unknown error')}")
            
            # Minimal delay between renames
            await asyncio.sleep(0.1)
            
    except Exception as e:
        logging.error(f"💥 Worker {worker_id} crashed: {e}")
    finally:
        await page.close()

async def live_stats_display(base_names, thread_url, task_count):
    """Display live statistics"""
    while True:
        async with stats_lock:
            os.system("cls" if os.name == "nt" else "clear")
            print(COLORS['cyan'] + "┌────────────────────────────────────────┐" + COLORS['reset'])
            print(COLORS['yellow'] + "│    INSTAGRAM GC RENAMER - LIVE STATS   │" + COLORS['reset'])
            print(COLORS['cyan'] + "└────────────────────────────────────────┘" + COLORS['reset'])
            print()
            print(COLORS['blue'] + f"📱 Thread URL: {thread_url}" + COLORS['reset'])
            print(COLORS['magenta'] + f"👥 Active Workers: {task_count}" + COLORS['reset'])
            print(COLORS['white'] + f"📝 Base Names: {len(base_names)}" + COLORS['reset'])
            print(COLORS['cyan'] + f"🔢 Used Names: {len(used_names)}" + COLORS['reset'])
            print(COLORS['white'] + f"🎯 Total Attempts: {success_count + fail_count}" + COLORS['reset'])
            print()
            print(COLORS['green'] + f"✅ Success: {success_count}" + COLORS['reset'] + "  " + 
                  COLORS['red'] + f"❌ Failed: {fail_count}" + COLORS['reset'])
            print(COLORS['yellow'] + f"📊 Success Rate: {(success_count/(success_count + fail_count)*100 if (success_count + fail_count) > 0 else 0):.1f}%" + COLORS['reset'])
            print()
            print(COLORS['cyan'] + "Press Ctrl+C to stop" + COLORS['reset'])
        
        await asyncio.sleep(0.5)

async def main():
    parser = argparse.ArgumentParser(description="Instagram Group Chat Renamer - Ultra Fast Async Version")
    parser.add_argument('--session-id', required=True, help='Instagram session ID')
    parser.add_argument('--thread-url', required=True, help='Target group chat URL')
    parser.add_argument('--names', required=True, help='Comma-separated list of base names')
    parser.add_argument('--tasks', type=int, default=3, help='Number of parallel workers (default: 3)')
    parser.add_argument('--headless', default='true', help='Run in headless mode (true/false)')
    
    args = parser.parse_args()
    
    # Parse names
    base_names = [name.strip() for name in args.names.split(',') if name.strip()]
    if not base_names:
        logging.error("No valid names provided")
        return
    
    headless = args.headless.lower() == 'true'
    task_count = args.tasks
    
    logging.info(f"Starting {task_count} parallel workers with {len(base_names)} base names")
    
    async with async_playwright() as p:
        # Launch browser with optimized settings
        browser = await p.chromium.launch(
            headless=headless,
            args=[
                '--no-sandbox',
                '--disable-gpu',
                '--disable-dev-shm-usage',
                '--disable-blink-features=AutomationControlled',
                '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            ]
        )
        
        # Create context with session
        context = await browser.new_context(
            viewport=None,
            locale="en-US",
            extra_http_headers={
                "Referer": "https://www.instagram.com/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
        
        # Add session cookie
        await context.add_cookies([{
            "name": "sessionid",
            "value": args.session_id,
            "domain": ".instagram.com",
            "path": "/",
            "httpOnly": True,
            "secure": True,
            "sameSite": "Lax"
        }])
        
        # Start worker tasks
        worker_tasks = [
            asyncio.create_task(rename_worker(context, args.thread_url, base_names, i+1))
            for i in range(task_count)
        ]
        
        # Start stats display
        stats_task = asyncio.create_task(
            live_stats_display(base_names, args.thread_url, task_count)
        )
        
        try:
            # Wait for all tasks
            await asyncio.gather(*worker_tasks, stats_task)
        except KeyboardInterrupt:
            logging.info("🛑 Stopping all workers...")
        finally:
            # Cleanup
            for task in worker_tasks:
                task.cancel()
            stats_task.cancel()
            
            await browser.close()
            logging.info("🎯 Script finished")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Script stopped by user")
    except Exception as e:
        logging.error(f"💥 Fatal error: {e}")
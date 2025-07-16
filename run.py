import asyncio
import sys
import os

from aiohttp import web

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.main import main


# =========================================================================
# CORE USER INTERACTION HANDLERS (High Priority)
# These methods directly respond to Telegram updates (commands, messages, callbacks).
# =========================================================================


async def dummy_server():
    """Starts a dummy web server to keep the Render service alive."""

    async def handle(request):
        """Handles incoming web requests."""
        return web.Response(text="Telegram bot is running on Render!")

    app = web.Application()
    app.router.add_get("/", handle)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.environ.get("PORT", 8000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def run_all():
    """Runs both the dummy server and the main bot application concurrently."""
    await asyncio.gather(dummy_server(), main())


if __name__ == "__main__":
    try:
        asyncio.run(run_all())
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

import os
import logging
import time

logger = logging.getLogger("scrim-bot")

def load_cogs(bot):
    """Recursively load all cogs from "commands" and "listeners" directories with timing."""
    timings = []

    for folder in ["commands", "listeners"]:
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("_"):
                    extension = root.replace("/", ".").replace("\\", ".") + "." + filename[:-3]
                    start = time.perf_counter()
                    try:
                        bot.load_extension(extension)
                        elapsed = (time.perf_counter() - start) * 1000  
                        timings.append((extension, elapsed))
                        logger.info(f"✅ Loaded extension: {extension} ({elapsed:.2f}ms)")
                    except Exception as e:
                        logger.error(f"❌ Failed to load extension {extension}: {e}")

    # After all cogs loaded, print timing summary
    if timings:
        timings.sort(key=lambda x: x[1], reverse=True)
        logger.info("📈 Extension Load Times:")
        for ext, ms in timings:
            logger.info(f"  {ext}: {ms:.2f} ms")

def reload_cogs(bot):
    """Unload all cogs, reload all cogs, and load new cogs if needed. Return (success, failed, timings)."""

    success = []
    failed = []
    timings = []

    for folder in ["commands", "listeners"]:
        for root, dirs, files in os.walk(folder):
            for filename in files:
                if filename.endswith(".py") and not filename.startswith("_"):
                    extension = root.replace("/", ".").replace("\\", ".") + "." + filename[:-3]

                    start = time.perf_counter()
                    try:
                        if extension in bot.extensions:
                            bot.unload_extension(extension)

                        bot.load_extension(extension)
                        elapsed = (time.perf_counter() - start) * 1000
                        timings.append((extension, elapsed))
                        success.append(extension)
                    except Exception as e:
                        failed.append((extension, str(e)))

    return success, failed, timings
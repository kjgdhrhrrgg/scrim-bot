import os

def setup(bot):
    for filename in os.listdir(os.path.dirname(__file__)):
        if filename.endswith(".py") and filename != "__init__.py":
            extension = f"commands.admin.{filename[:-3]}"
            bot.load_extension(extension)
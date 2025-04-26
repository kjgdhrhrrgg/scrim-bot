import discord

print("Pycord version:", discord.__version__)
print("\nAttributes in discord module:\n")

for attr in dir(discord):
    print(attr)

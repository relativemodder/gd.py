"""Example that shows downloading a song.
Author: NeKitDS.
"""

import gd

client = gd.Client()  # an entry point


async def main() -> None:
    while True:
        query = input("Enter song ID: ")

        try:
            # fetch a song and install it
            song = await client.get_ng_song(int(query))
            data = await song.download()

        except ValueError:
            print("Invalid type. Expected an integer.")
        except gd.MissingAccess:
            print("Song was not found.")

        else:
            # save a song and print a message
            name = f"{song.id}.mp3"
            with open(name, "wb") as file:
                file.write(data)
            print(f"Installed {song.name!r} by {song.author!r} -> {name!r}.")


# gracefully run
try:
    client.run(main())
except KeyboardInterrupt:
    pass

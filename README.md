<div align="center" style="font-size: 30px; font-weight: bold; height: 50px">Discord Taskbot</div>


*Task management utility for small programming teams.*

### About
Status: **Alpha**. See [Development](#development) for more.

**Feature overview**
- Create new projects and assign them to a text channel
- Add new tasks with a title and a short description
- Interact with the task through reactions:
    - Set status to 'Pendig', 'In Progress', 'Merge ready' and 'Done'
    - Self-assign tasks
    - Discuss the task in a separate thread
    - Customize reaction emojis

- Use discords native app commands with an intuitive command set
- Discord modals for nice task editing, overviews and user experience

### Getting Started

Create your own discord bot through the developer portal (see the official [docs](https://discord.com/developers/docs/getting-started#creating-an-app) for more details), and copy the generated bot token. Rename .env.default to .env. Paste the copied token into the .env file behind TOKEN=.

Add your bot to a discord server. The bot will need two scopes: bot and applications.command. The required permission id is 326417639488 (Send Messages, Create Public Threads, Send Messages in Threads, Manage Messages, Manage Threads, Embed Links, Attach Files, Read Message History and Add Reactions. Again, read the official docs for more information on how to add your bot to your server. You can change the bot's permissions in your server settings later in case you missed something.

Next, choose a way of executing the bot and follow the steps respectively.

#### PIP (normal execution)
1. `pip3 install .`
2. `discord-taskbot run <envfile here>`

Instead of *discord-taskbot* you can also use the shorter alias *discordtb*.

#### Docker (yet untested)
1. `./build-docker.sh`
2. `docker run -v $(PWD)/.env:/data/.env discord_taskbot`

If you don't specify an environment variable named 'TOKEN' (which will be done automatically when you attach the .env file to your execution) the script will throw a NoToken exception.

### Documentation
> Haha, nope.


### Development
*discord-taskbot* is in **alpha** development.

This means you can use the bot and it should work, however longterm stability is not ensured yet. The codebase is in need of simplification and refactoring.

Below you can find a basic ToDo-list on all things that need to be done:

- [ ] Code refactoring
- [ ] Global code documentaton
- To be continued...


### Contributing
**Feel free!** If you have ideas for improvements open a new issue per improvement. If you want to contribute some code do so by creating a merge request.

### FAQ
*How does the bot ensure data persistence?*
> The script automatically creates and uses an on-storage SQLite database.

*Why do I need to create my own Discord bot to run this bot? For me it is way easier to just get the invite-link and use this bot on my server.*
> This is **a small sideproject that I open sourced** so the world can use it if it wants to use it. Its primary target are developers, so it shouldn't be a problem for them to read the documentation and add the bot manually.
> 
> If I would host a global instance of this bot, I would be responsible for providing a smooth bot experience, constant support, server uptime + security and ensure your data's privacy. As a student and hobbyist I simply don't want to take this burden on me and risk potential security breaches.
> 
> Additionally, a global bot would increase the complexity and require me to do more coding and testing (serve multiple discord servers, no messing up of multiple datastreams), which I'm currently not interested in. Also, no time.

*Which license does your code have?*
> MIT.

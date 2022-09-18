<div align="center" style="font-size: 30px; font-weight: bold; height: 50px">Discord Taskbot</div>


*Task management utility for small programming teams.*
**README is in development. Documentation and decisions may change!**

__TOC__

### Features
- Create new projects and assign them to a text channel
- Add new tasks with a title and a short description
- Interact with the task through reactions:
    - Set status to 'Pendig', 'In Progress', 'Merge ready' and 'Done'
    - Self-assign tasks
    - Discuss the task in a separate thread

- Use discords native app commands with an intuitive command set
- Discord modals for nice task editing, overviews and user experience

### Getting Started
> Coming soon.
> 
> `./build-docker.sh`
> 
> `docker run -v $(PWD)/.env:/data/.env discord_taskbot`
>
> Or just `pip3 install .` and then `discord-taskbot run <envfile here>`. *discordtb* is an alias for *discord-taskbot*.

### Documentation
> Haha, nope.

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

*Which licence does your code have?*
> During pre-alpha development, the entire codebase is propietary. Any usage, replicating or commercializing is forbidden.

# Thug's Rumāl

From Wikipedia, the free encyclopedia:
> A rumāl is a piece of clothing similar to a handkerchief or bandana. [...] The rumāl was used by the Thugs in India as a method of strangulation. A coin was knotted in one end of the scarf, and would be swung around the neck of the victim; who would then be strangled in the most brutal and abhorrent manner.

This project aims to be [Thug](http://buffer.github.io/thug/)'s dress - providing a convenient web GUI - but also its weapon, as it should provide a set of tools that should enrich Thug's output with new metadata and allow for correlation of results.

While it is perfectly possible to use it as a simple web GUI for Thug on your own computer, with you as the only user, Rumāl has been designed to support multi-user environments, just like a sort of social network, allowing you to share your results and your settings with other users and groups.

## Basic usage

### Install

To get Rumāl's source code, you can run the following command:

    $ git clone git@github.com:thugs-rumal/rumal.git

**Please consider using VirtualEnv from now on, especially if you already have other projects running on Django versions other than 1.9**. Installing VirtualEnv is extremely easy:

    $ sudo pip install virtualenv

Actually, you only need sudo if you're installing `virtualenv` globally (which I suggest you to do). Now, `cd` to Rumāl's root directory to create and activate your virtual environment:

    $ cd rumal
    $ virtualenv venv
    $ source venv/bin/activate

That's all. The first command will create a folder named `venv`, with a copy of the Python executable, pip and some other tools; the second command will activate the virtual environment for you. From now on, every time you run `pip install`, the requested modules will be installed locally, without touching your global Python environment.
When you're done with Rumāl, just run `deactivate` to exit from `venv`. Please also consider using [Autoenv](https://github.com/kennethreitz/autoenv) to automatically activate your virtual environment every time you enter the folder (and to automatically deactivate it when you leave).

Now, you can install Rumāl's dependencies by running the following command from Rumāl's root directory. **WARNING: Rumāl requires specific versions of some libraries such as Django 1.9. If you've got other projects running on the same box, please consider using VirtualEnv (see above) if you didn't already!**

    $ pip install -r requirements.txt

Now you can setup the database (which, for now, uses SQLite as the backend) and create your superuser by running (from Rumāl's root directory):

    $ python manage.py migrate
    $ python manage.py createsuperuser

### Basic configuration

Before running Rumāl's front-end, you will need to let it know how to reach the back-end's APIs. You will need to configure the back-end by following the instructions on its own repo, that you will find here: https://github.com/thugs-rumal/rumal_back.

Once the back-end is ready, you will need to configure the front-end by creating a new configuration file by running (from the front-end's root):

    $ cp conf/backend.conf.example conf/backend.conf

This file will contain the following values:

    [backend]
    host = "http://localhost:8080"
    api_key = "testkey"
    api_user = "testuser"

Please change them according on how you configured the back-end.

### Running Rumal's front-end

The front-end module is composed of three separate daemons: `fdaemon`, `enrich` and the web server.

Both `fdaemon` and `enrich` were both developed as management commands, so you can run them by using:

    $ python manage.py fdaemon > /dev/null 2>&1 &
    $ python manage.py enrich > /dev/null 2>&1 &

Of course, redirecting the output to a log file or, better yet, using separate consoles and letting them run without detaching will give you a lot more info about what's happening.

Running the web server is as simple as doing:

    $ python manage.py runserver

Or, if you want your server to be reachable from the external network:

    $ python manage.py runserver 0.0.0.0:8000

Now you can connect to the GUI by pointing your browser to http://127.0.0.1:8000/ (or to whatever IP/port you chose).

## Contributing

### Random thoughts

* The **server-side** part of the GUI should be as lightweight as possible. We should try keeping the overall number of Django views low and to work on extensive APIs.
* Rendering should be performed at **client-side**, trying to avoid full page refreshes in favor of API calls via JQuery and subsequent DOM modifications.
* Let's think of Rumāl as a sort of **social network**. Elements (analyses, results, metadata, configurations) should be easily shared with other users/groups or even made public. Look at the `user` (owner), `sharing_model` and `sharing_groups` fields of `Task` and `Proxy` in `interface/models.py` to get an idea of what I mean.

# Thug's Rumāl

From Wikipedia, the free encyclopedia:
> A rumāl is a piece of clothing similar to a handkerchief or bandana. [...] The rumāl was used by the Thugs in India as a method of strangulation. A coin was knotted in one end of the scarf, and would be swung around the neck of the victim; who would then be strangled in the most brutal and abhorrent manner.

This project aims to be [Thug](http://buffer.github.io/thug/)'s dress - providing a convenient web GUI - but also its weapon, as it should provide a set of tools that should enrich Thug's output with new metadata and allow for correlation of results.

While it is perfectly possible to use it as a simple web GUI for Thug on your own computer, with you as the only user, Rumāl has been designed to support multi-user environments, just like a sort of social network, allowing you to share your results and your settings with other users and groups.

## Basic usage

### Install

Rumāl needs to make sure you are using a supported Thug version, to avoid any incompatibilities in arguments and behaviours. To do so, Thug was included as a submodule.

To clone both Rumāl and Thug at once, you can run the following command:

    $ git clone --recursive git@github.com:pdelsante/rumal.git

**Please consider using VirtualEnv from now on, especially if you already have other projects running on Django versions other than 1.7**. Installing VirtualEnv is extremely easy:

    $ sudo pip install virtualenv

Actually, you only need sudo if you're installing `virtualenv` globally (which I suggest you to do). Now, `cd` to Rumāl's root directory to create and activate your virtual environment:

    $ cd rumal
    $ virtualenv venv
    $ source venv/bin/activate

That's all. The first command will create a folder named `venv`, with a copy of the Python executable, pip and some other tools; the second command will activate the virtual environment for you. From now on, every time you run `pip install`, the requested modules will be installed locally, without touching your global Python environment.
When you're done with Rumāl, just run `deactivate` to exit from `venv`. Please also consider using [Autoenv](https://github.com/kennethreitz/autoenv) to automatically activate your virtual environment every time you enter the folder (and to automatically deactivate it when you leave).

Before any further setup on Rumāl's part, you will need to set up Thug first. Please refer to [Thug's own documentation](http://buffer.github.io/thug/). **Please make sure you fully configure MongoDB and let Thug's MongoDB logger enabled.**

Now, you can install Rumāl's own dependencies by running the following command from Rumāl's root directory. **WARNING: Rumāl requires specific versions of some libraries such as Django 1.7. If you've got other projects running on the same box, please consider using VirtualEnv (see above) if you didn't already!**

    $ pip install -r requirements.txt

Now you can setup the database (which, for now, uses SQLite as the backend) and create your superuser by running (from Rumāl's root directory):

    $ python manage.py migrate
    $ python manage.py createsuperuser

### The web server

Running the web server is as simple as doing:

    $ python manage.py runserver

Or, if you want your server to be reachable from the external network:

    $ python manage.py runserver 0.0.0.0:8000

Now you can connect to the GUI by pointing your browser to http://127.0.0.1:8000/ (or to whatever IP/port you chose).

### The backend daemon

The backend daemon still has to be implemented from scratch, so there isn't much to do about it for now.

### Importing tasks from your existing MongoDB

If you have any existing analyses in your MongoDB instance (which is normal if you previously ran another Thug instance on the same machine you're working on), you can import them into Rumāl by running:


    $ cd test_utils
    $ ./import_existing_analyses.py


This should make things a bit easier if you're going to test the web GUI or work on its code.

## Contributing

### Random thoughts

#### Web GUI:

* The **server-side** part of the GUI should be as lightweight as possible. We should try keeping the overall number of Django views low and to work on extensive APIs.
* Rendering should be performed at **client-side**, trying to avoid full page refreshes in favor of API calls via JQuery and subsequent DOM modifications.
* Let's think of Rumāl as a sort of **social network**. Elements (analyses, results, metadata, configurations) should be easily shared with other users/groups or even made public. Look at the `user` (owner), `sharing_model` and `sharing_groups` fields of `Task` and `Proxy` in `interface/models.py` to get an idea of what I mean.

#### Backend Daemon:

* **Very important**: Thug has a peculiar way of using python's `logging` module to create a sort of global variable that is maintained by the interpreter. Almost everything in Thug is added to the `log` instance so that it can be accessed from any point. This will most probably cause problems when trying to run multiple Thug instances at once (e.g. using threads or parallel processes).
* The daemon's main process should simply:
    * `from ThugAPI import ThugAPI`
    * get Thug's almighty logger by running a `log = logging.getLogger("Thug")`
    * instantiate the `ThugAPI` object with the appropriate arguments (taken from the `Task` model)
    * run the analysis
    * retrieve the MongoDB's `ObjectID` value from the logger by doing accessing `log.ThugLogging.modules['mongodb'].analysis_id`
    * save the ObjectID value in the `Task` object.

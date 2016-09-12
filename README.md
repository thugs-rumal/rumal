# Thug's Rumāl

From Wikipedia, the free encyclopedia:
> A rumāl is a piece of clothing similar to a handkerchief or bandana. [...] The rumāl was used by the Thugs in India as a method of strangulation. A coin was knotted in one end of the scarf, and would be swung around the neck of the victim; who would then be strangled in the most brutal and abhorrent manner.

This project aims to be [Thug](http://buffer.github.io/thug/)'s dress - providing a convenient web GUI - but also its weapon, as it should provide a set of tools that should enrich Thug's output with new metadata and allow for correlation of results.

While it is perfectly possible to use it as a simple web GUI for Thug on your own computer, with you as the only user, Rumāl has been designed to support multi-user environments, just like a sort of social network, allowing you to share your results and your settings with other users and groups.

## Documentation

Documentation about Rumal architecture, installation and usage can be found at [http://thugs-rumal.github.io/](http://thugs-rumal.github.io/)

## Contributing

### Random thoughts

* The **server-side** part of the GUI should be as lightweight as possible. We should try keeping the overall number of Django views low and to work on extensive APIs.
* Rendering should be performed at **client-side**, trying to avoid full page refreshes in favor of API calls via JQuery and subsequent DOM modifications.
* Let's think of Rumāl as a sort of **social network**. Elements (analyses, results, metadata, configurations) should be easily shared with other users/groups or even made public. Look at the `user` (owner), `sharing_model` and `sharing_groups` fields of `Task` and `Proxy` in `interface/models.py` to get an idea of what I mean.

## License

Rumal is licensed under the GPLv2 or later. Rumal releases also include and make use of other libraries with their own separate licenses.

The license is available [here](https://github.com/pdelsante/rumal/blob/master/COPYING).

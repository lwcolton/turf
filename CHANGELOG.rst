v2.0.0:
- Config must now be instantiated into an object, class methods are gone
- Config is now a subclass of UserDict and should be treated like a dictionary (section() is gone)
- Config now loads all sections (refresh) by default when created
- Remove SingleFileConfig
- Remove is_debug
- Config is now refreshed when you access a top level key
- Added refresh_seconds parameter to control how often the config 
    is refreshed upon access (default 60 seconds)
- When a section is accessed, only that section is refreshed (for efficiency)
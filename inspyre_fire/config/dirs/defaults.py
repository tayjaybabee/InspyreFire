from platformdirs import PlatformDirs
from inspyre_fire.common import PACKAGE_NAME as APP_NAME
from inspyre_fire.common.about.author import SOFTWARE_ORG as AUTHOR
from pathlib import Path


print(f'APP_NAME: {APP_NAME}')
print(f'AUTHOR: {AUTHOR}')

class DefaultDirs(PlatformDirs):
    def __init__(self):
        super().__init__(APP_NAME, AUTHOR.name)

    def __getattribute__(self, name):
        # Intercept attribute access
        value = super().__getattribute__(name)
        # If the attribute name contains '_dir' and is a property
        if '_dir' in name and isinstance(value, (str, Path)):
            # Convert the result to a Path object before returning
            return Path(value)
        return value

    @property
    def user_temp_dir(self):
        return self.user_cache_dir




DEFAULT_DIRS = DefaultDirs()


del DefaultDirs
del APP_NAME
del AUTHOR


__all__ = [
    'DEFAULT_DIRS'
]

import configparser
import os
import time
from inspyre_toolbox.syntactic_sweets.classes.decorators.type_validation import validate_type
from pathlib import Path
from typing import Optional, Union
from warnings import warn
from inspyre_fire.config.constants import CONFIG_SPECS, CONFIG_SYSTEM_NAMES, SPEC_FILE_PATHS, CONFIG_SYSTEM_MAP, FILE_SYSTEM_DEFAULTS
from inspyre_fire.config.utils import wait_for_changes
from inspyre_fire.config.utils.types import convert_str_to_type, TYPE_MAPPING
from inspyre_fire.config.errors import (
ConfigBackupDirectoryNonExistentError, ConfigDirectoryNonExistentError, InvalidConfigSystemError
    )



class ConfigFactory:
    _instances = {}
    _initializing = set()

    @classmethod
    def get_config_system_by_instance_id(cls, instance_id):
        for config_system, instance in cls._instances.items():
            if instance_id(instance) == instance_id:
                return config_system

    @classmethod
    def find_instance_by_id(cls, target_id):
        for instance in cls._instances.values():
            if id(instance) == target_id:
                return instance

    def __new__(cls, config_system: str, *args, **kwargs):
        config_system = config_system.lower()
        if config_system not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[config_system] = instance

        return cls._instances[config_system]

    def __init__(
            self,
            config_system: str,
            auto_load: Optional[bool] = False,
            skip_auto_saving: Optional[bool] = False,
            config_dir_path: Optional[Union[str, Path]] = FILE_SYSTEM_DEFAULTS['dirs']['config'],
            skip_reload_on_change: Optional[bool] = False,
            ):
        """
        Initialize a ConfigFactory object.

        Parameters:
            config_system (str):
                The name of the configuration system to use. Must be one of the keys in :attr:`CONFIG_SYSTEMS`.

        """
        self._initialized = False
        self._initialize_attributes(
                config_system,
                auto_load,
                skip_auto_saving,
                config_dir_path,
                skip_reload_on_change,
            )
        self._initialized = True


    def _initialize_attributes(
            self,
            config_system: str,
            auto_load: Optional[bool] = False,
            skip_auto_saving: Optional[bool] = False,
            config_dir_path: Optional[Union[str, Path]] = FILE_SYSTEM_DEFAULTS['dirs']['config'],
            skip_reload_on_change: Optional[bool] = False,
        ):
        def get_config_systems():
            from inspyre_fire.config import CONFIG_SYSTEMS

            return CONFIG_SYSTEMS

        self.__auto_save = not skip_auto_saving
        self.__config_system = config_system.lower()
        self.__config_changed = False
        self.__file_modified = None
        self.__reload_file_on_change = not skip_reload_on_change
        self.__config_dir_path = Path(config_dir_path).expanduser().resolve().absolute()
        self.__loaded_config = False

        self.__config_systems = get_config_systems()
        self.__config = configparser.ConfigParser()
        self.__config_spec = CONFIG_SPECS[self.__config_system]

        if auto_load:
            self.load_config_if_exists()

        if auto_load and not self.__loaded_config:
            self.create_config_file()

    def _return_from_defaults(self, item):
        from inspyre_fire.config.utils import search_file_for_user_line
        from warnings import warn

        if self.config_file_path and self.config_file_path.exists():
            if not search_file_for_user_line(self.config_file_path):
                warn(f"User configuration not found in '{self.config_file_path}'.")
            else:
                warn(f"Attribute '{item}' not found in '{self.__class__.__name__}' object. Returning default value.")
        else:
            warn(f"Configuration file not found. Returning default value for '{item}'.")

        if not item in self.__dict__['_ConfigFactory__config_spec'].defaults:
            warn(f"Attribute '{item}' not found in '{self.__class__.__name__}' object. Returning None.")
            return None

        return self.__dict__['_ConfigFactory__config_spec'].defaults[item]


    @property
    def __is_cache_config(self):
        """
        Check if the configuration system is the cache configuration system.

        Returns:
            bool:
                True if the configuration system is the cache configuration system, False otherwise.

        """
        if 'alternate_directories' in ConfigFactory._initializing:
            return True

        if self.__config_system == 'alternate_directories':
            return True

    def __getattr__(self, item):
        section_name = self.determine_section()
        self._check_section(section_name)
        if not self._initialized:
            raise AttributeError(f"'{self.__class__.__name__}' object is not initialized yet")

        #print(self.__dict__['_ConfigFactory__config'].defaults())

        res = None

        if item in self.__dict__:
            res = self.__dict__[item]
        elif item in self.__dict__['_ConfigFactory__config'].defaults():
            res = self.__dict__['_ConfigFactory__config'].get(section_name, item)
        elif item in self.__dict__['_ConfigFactory__config_spec'].defaults:
            res = self._return_from_defaults(item)

        if item in self.__dict__['_ConfigFactory__config_spec'].spec:
            res_type = self.__dict__['_ConfigFactory__config_spec'].spec[item]['type']
            if res_type in TYPE_MAPPING:
                return convert_str_to_type(res, res_type)

        if res:
            return res

        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{item}'")


    def __setattr__(self, key, value):
        if key in {'_initialized', '_instances', '_initializing'} or not self._initialized:
            return object.__setattr__(self, key, value)
        elif key in self.__dict__:
            self.__dict__[key] = value
            return
        elif key in self.__dict__['_ConfigFactory__config'].defaults():
            section_name = self.determine_section()
            self._check_section(section_name)
            self.__dict__['_ConfigFactory__config'].set(section_name, key, value)
            self.__config_changed = True

        if key in self.config.defaults():
            if self.__config_changed and self.__auto_save:
                self.save_config()
                self.load_config()

    def _check_section(self, section: str = 'USER', do_not_create: bool = False):
        """
        Check if the specified section exists in the config object.

        Parameters:
            section (str):
                The name of the section to check for.

            do_not_create (bool):
                If True, the section will not be created if it does not exist.

        Returns:
            bool:
                True if the section exists, False otherwise. This will also return True if the section was created
                and False if it was not, depending on the value of :param:`do_not_create`.
        """

        section = section.upper()

        if not self.config.has_section(section) and not do_not_create:
            self.config.add_section(section)

        return self.config.has_section(section)

    @property
    def config(self):
        """
        Get the ConfigParser object.

        Returns:
            configparser.ConfigParser:
                The ConfigParser object.

        """
        return self.__config

    @config.setter
    @validate_type(configparser.ConfigParser)
    def config(self, new: configparser.ConfigParser):
        """
        Set the ConfigParser object.

        Parameters:
            new (configparser.ConfigParser):
                The new ConfigParser object to set.

        Returns:
            None
        """
        self.__config = new

    @property
    def config_changed(self) -> bool:
        """
        Get the configuration changed flag.

        This flag is set to True when the configuration is changed and should be saved to disk.

        Returns:
            bool:
                True if the configuration has been changed, False otherwise.

        """
        return self.__config_changed

    @config_changed.setter
    @validate_type(bool)
    def config_changed(self, new: bool):
        """
        Set the configuration changed flag.

        Parameters:
            new:
                The new value of the configuration changed flag.

        Returns:
            None

        """
        self.__config_changed = new

    @property
    def config_dir_path(self):
        """
        Get the path to the directory containing the configuration file.

        Returns:
            Path:
                The path to the directory containing the configuration file.
        """
        return self.__config_dir_path

    @property
    def config_file_modified(self):
        """
        Get the file modified flag.

        Returns:
            bool:
                True if the configuration file has been modified, False otherwise.
        """
        return self.__file_modified

    @config_file_modified.setter
    @validate_type(bool)
    def config_file_modified(self, new: bool):
        """
        Set the file modified flag.

        Parameters:
            new:
                The new value of the file modified flag.

        Returns:
            None
        """
        self.__file_modified = new

        if self.__file_modified and self.__reload_file_on_change:
            self.reload_config()

    @property
    def config_file_name(self) -> str:
        """
        Get the name of the INI file.

        Returns:
            str:
                The name of the INI file.

        """
        return f"{self.__config_system}.ini" if self.__config_system != 'alternate_directories' else 'cache.ini'

    @property
    def config_file_path(self) -> Optional[Path]:
        """
        Get the path to the INI file.

        Returns:
            Path:
                The path to the INI file.
        """

        if not self.__config_system:
            return None

        return Path(f"{self.config_dir_path}/{self.config_file_name}")

    @config_file_path.setter
    def config_file_path(self, new: Union[str, Path]) -> None:
        """
        Set the path to the INI file.

        Parameters:
            new (Union[str, Path]):
                The new path to the INI file.

        Returns:
            None

        """
        new_path = Path(new)

        if new_path != self.__config_systems[self.__config_system]['default']:
            raise ValueError(f"Invalid path: '{new}'\nTry setting this through config.set_config_file_path()")

    @property
    def config_spec(self) -> dict:
        """
        Get the configuration specification.

        Returns:
            dict:
                The configuration specification.
        """
        return self.__config_spec

    @config_spec.setter
    @validate_type(dict)
    def config_spec(self, new: dict) -> None:
        """
        Set the configuration specification.

        Parameters:
            new (dict):
                The new configuration specification.

        Returns:
            None
        """
        self.__config_spec = new

    @property
    def config_spec_file_path(self) -> Optional[Path]:
        """
        Get the path to the JSON file containing the configuration specification.

        Returns:
            Path:
                The path to the JSON file containing the configuration specification.
        """
        if self.config_spec:

            try:
                return self.config_spec.file_path
            except AttributeError:
                return None

    @property
    def config_system(self) -> str:
        """
        Get the configuration system.

        Returns:
            str:
                The configuration system.
        """
        return self.__config_system

    @config_system.setter
    @validate_type(str)
    def config_system(self, new: str) -> None:
        """
        Set the configuration system.

        Parameters::
            new:
                The new configuration system.

        Returns:
            None
        """
        if new.lower() not in CONFIG_SYSTEM_NAMES:
            raise InvalidConfigSystemError(new, CONFIG_SYSTEM_NAMES)

        self.__config_system = new.lower()

    @property
    def defaults(self) -> dict:
        """
        Get the default values from the configuration specification.

        Returns:
            dict:
                The default values from the configuration specification
        """
        if self.__config_spec:
            return self.__config_spec.defaults
        else:
            return {}

    @property
    def loaded_config(self) -> bool:
        """
        Check if the configuration has been loaded.

        Returns:
            bool:
                True if the configuration has been loaded, False otherwise.

        """
        return self.__loaded_config

    @property
    def reload_file_on_change(self) -> bool:
        """
        Get the reload file on change flag.

        Returns:
            bool:
                True if the configuration file should be reloaded when it is changed, False otherwise.
        """
        return self.__reload_file_on_change

    @reload_file_on_change.setter
    @validate_type(bool)
    def reload_file_on_change(self, new: bool) -> None:
        """
        Set the reload file on change flag.

        Parameters:
            new (bool):
                The new value of the reload file on change flag.

        Returns:
            None
        """
        self.__reload_file_on_change = new
        if new and self.config_file_modified:
            self.reload_config()

    # Property aliases
    config_loaded = property(lambda self: self.loaded_config)
    loaded = property(lambda self: self.loaded_config)

    @property
    def user_config_section_name(self) -> str:
        """
        Get the name of the user configuration section.

        Returns:
            str:
                The name of the user configuration section.
        """
        return 'USER' if not self.__is_cache_config else 'CACHE'

    def backup_config(
            self,
            backup_dir: Optional[Union[str, Path]] = FILE_SYSTEM_DEFAULTS['dirs']['config'] / 'backups',
            backup_name: Optional[str] = None,
            backup_ext: Optional[str] = '.bak',
            do_not_create_dir: Optional[bool] = False,
            overwrite: Optional[bool] = False
            ) -> None:
        """
        Backup the configuration file.

        Parameters:

            backup_dir (Union[str, Path]):
                The directory to place the backup file in.

            backup_name (str):
                The name to give the backup file. If None, the backup file will be named after the configuration file,
                with the current date and time appended.

            backup_ext (str):
                The extension to give the backup file. If None, the extension will be '.bak'.

            do_not_create_dir (bool):
                If True, the backup directory will not be created if it does not exist. This will raise a
                ConfigBackupDirectoryNonExistentError if the directory does not exist.

            overwrite:

        Returns:

        """

        backup_dir = Path(backup_dir)

        # If the backup directory does not exist, create it.
        if not backup_dir.exists() and not do_not_create_dir:
            backup_dir.mkdir(parents=True)

        # ...or raise an error if it does not exist, and we are prohibited creating it.
        elif not backup_dir.exists() and do_not_create_dir:
            raise ConfigBackupDirectoryNonExistentError(
                    backup_dir,
                    "Set `do_not_create_dir` to `False` to create the directory."
                    )

        # Determine the name of the backup file.
        if not backup_name:
            backup_name = self.config_file_path.stem
            backup_file_name = f'{backup_name}_{time.strftime("%Y%m%d_%H%M%S")}{backup_ext}'
        else:
            backup_file_name = f'{backup_name}{backup_ext}' if not backup_name.endswith(backup_ext) else backup_name

        # Create the full path to the backup file.
        backup_file_path = backup_dir / backup_file_name

        # If the backup file already exists, raise an error if we are not allowed to overwrite it.
        if not overwrite and backup_file_path.exists():
            raise FileExistsError(f"Backup file already exists: {backup_file_path}")

        # Otherwise, backup the configuration file.
        with open(self.config_file_path, 'r') as config_file:
            with open(backup_file_path, 'w') as backup_file:
                backup_file.write(config_file.read())

        print('Created backup')

    def create_config_directory(self, fail_if_exists=False) -> None:
        """
        Create the parent directory for the configuration (ini) file.

        Returns:
            None
        """
        self.config_file_path.parent.mkdir(parents=True, exist_ok=not fail_if_exists)

    def create_config_file(self) -> None:
        """
        Create a configuration file from the configuration specification.

        Returns:
            None

        Raises:
            FileExistsError:
                Raised when the INI file already exists. This is to prevent overwriting existing configuration files. It
                is caught and a warning is issued before returning without creating a new configuration file.
        """
        try:
            if self.config_file_path.exists():
                raise FileExistsError(f'The file {self.config_file_path} already exists.')

        except FileExistsError as e:
            warn(f"FileExistsError: {e} - Returning without creating a new config file.")
            return

        if not self.config.defaults():
            self.generate_config()

        self.save_config(skip_backup=True)

    def delete_config_file(self) -> None:
        """
        Delete the configuration file.

        Returns:
            None
        """
        self.config_file_path.unlink()

    def determine_section(self):
        if self.__dict__['_ConfigFactory__config_system'] == 'alternate_directories':
            return 'CACHE'
        return 'USER'

    def generate_config(self) -> None:
        """
        Generate a ConfigParser object from the configuration specification.

        The ConfigParser object will have the default values from the configuration specification and will be
        ready to be saved to an INI file. (Use :meth:`ConfigFactory.save_config` to save the configuration to an INI file.)

        Returns:
            None
        """
        if not self.defaults:
            raise ValueError("No defaults found in configuration specification.")
        self.config['DEFAULT'] = self.defaults

    def load_config(self) -> None:
        """
        Load the configuration from the INI file.

        Returns:
            None
        """
        self.config.read(self.config_file_path)
        self.__loaded_config = True

        self.sync_config_with_spec()

    def load_config_if_exists(self):
        """
        Load the configuration from the INI file if it exists.

        Returns:
            None
        """
        if self.config_file_path.exists():
            self.load_config()

    def move_config_file(
            self,
            new: Union[str, Path],
            skip_backup: Optional[bool] = False,
            create_new_dir: Optional[bool] = False
            ) -> None:

        """
        Move the configuration file to a new location.

        Parameters:
            new (Union[str, Path]):
                The new location to move the configuration file to.

            skip_backup (bool):
                If True, a backup of the configuration file will not be created before moving it.

            create_new_dir (bool):
                If True, the directory containing the new location will be created if it does not exist.

        Returns:
            None
        """
        new = Path(new)
        if new.suffix:
            new = new.parent
        if not new.exists() and create_new_dir:
            new.mkdir(parents=True)
        elif not new.exists() and not create_new_dir:
            raise ConfigDirectoryNonExistentError(new.parent, "Set `create_new_dir` to `True` to create the directory.")
        if not skip_backup:
            self.backup_config()

        self.config_file_path.rename(new.joinpath(self.config_file_name))
        self.set_config_file_path(new)

    def open_config_directory(self):
        """
        Open the directory containing the configuration file.

        Returns:
            None

        """
        directory = str(self.config_file_path.parent)
        os.startfile(directory)

    def open_config_file(
            self,
            skip_backup: Optional[bool] = False,
            skip_wait_for_changes: Optional[bool] = False,
            skip_reload_on_change: Optional[bool] = not reload_file_on_change
            ) -> None:
        """
        Open the configuration file in the default text editor. Optionally, backup the configuration file, wait for
        changes, and reload the configuration on change.

        Parameters:
            skip_backup (bool):
                If True, a backup of the configuration file will not be created before opening it. Default is False.

            skip_wait_for_changes:
                If True, the system will not wait for you to make changes. Default is False. (Note: If this is `True`,
                the system will not automatically reload the configuration file whether you save changes or not.)

            skip_reload_on_change:
                If True, the system will not reload the configuration file if it is changed. Default is the opposite of
                the value of `reload_file_on_change`.

        Returns:
            None
        """

        if not skip_backup:
            self.backup_config()

        if not skip_wait_for_changes:
            self.__file_modified = wait_for_changes(self)
        else:
            config_fp_str = str(self.config_file_path)
            os.startfile(config_fp_str)
            return

        if self.config_file_modified and not skip_reload_on_change:
            self.load_config()

    def reload_config(self) -> None:
        """
        Reload the configuration from the INI file.

        Returns:
            None
        """
        self.load_config()

    def reset_to_defaults(self, skip_save: Optional[bool]) -> None:
        """
        Reset the configuration to the default values.

        Returns:
            None
        """
        self.config['USER'] = self.config['DEFAULT']
        if not skip_save:
            self.save_config()

    def restore_config_from_backup(self, backup_file: Union[str, Path] = None) -> None:
        """
        Restore the configuration from a backup file.

        Parameters:
            backup_file (Union[str, Path]):
                The path to the backup file to restore from, if no backup file is provided, the system will choose the
                most recent backup file for restoration.

        Returns:
            None
        """
        backup_file = Path(backup_file)

        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file does not exist: {backup_file}")

        with open(backup_file, 'r') as backup:
            with open(self.config_file_path, 'w') as config:
                config.write(backup.read())

        self.load_config()

    def save_config(self, skip_backup: Optional[bool] = False) -> None:
        """
        Save the configuration to an INI file.

        Returns:
            None
        """

        if self.config_file_path:
            print(f'Saving configuration to {self.config_file_path}')
            try:
                print(f'Checking if directory exists: {self.config_file_path.parent}')
                if not self.config_file_path.parent.exists():
                    raise FileNotFoundError(
                        f"Directory does not exist to place file in: {self.config_file_path.parent}")

            except FileNotFoundError as e:
                warn(f"FileNotFoundError: {e} - Attempting to create directory.")
                self.create_config_directory()

            print(f'File path: {self.config_file_path}')

            if self.config_file_path.exists():
                print(f'File exists: {self.config_file_path}')
                if not skip_backup:
                    print('Backing up configuration...')
                    try:
                        self.backup_config()
                        print('Backup created.')
                    except FileExistsError as e:
                        warn(f"FileExistsError: {e} - Skipping backup.")

                print('Deleting existing configuration file...')

                self.delete_config_file()

            with open(str(self.config_file_path), 'w') as configfile:
                self.config.write(configfile)
                configfile.close()

            if self.config_changed:
                self.config_changed = False

    def set_config_file_path(
            self,
            new: Union[str, Path],
            skip_backup: Optional[bool] = False,
            skip_move: Optional[bool] = False
        ) -> None:
        """
        Set the path to the INI file.

        Parameters:
            new (Union[str, Path]):
                The new path to the INI file.

        Returns:
            None
        """
        from inspyre_fire.config import NON_DEFAULT_DIRS

        new = Path(new).expanduser().resolve().absolute()
        old = self.config_file_path
        expected = self.config_systems[self.config_system]['default']

        ad = NON_DEFAULT_DIRS

        if new != expected:

            ad.config_dir = new
            ad.save_config()
        else:
            if new != old:
                ad.config = ''

    def sync_config_with_spec(self):
        """
        Synchronize the configuration with the configuration specification.

        Returns:
            None
        """
        if self.defaults.keys() != self.config.defaults().keys():
            warn("Configuration specification and configuration file do not match. Synchronizing...")
            self.generate_config()
            self.save_config()

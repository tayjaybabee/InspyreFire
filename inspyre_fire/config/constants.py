from inspyre_fire.config.spec import CONFIG_SPECS, CONFIG_SYSTEM_NAMES, SPEC_FILE_PATHS, CONFIG_SYSTEM_MAP
from inspyre_fire.config.dirs.defaults import DEFAULT_DIRS




FILE_SYSTEM_DEFAULTS = {
        'dirs': {
                'cache': DEFAULT_DIRS.user_cache_dir,
                'config': DEFAULT_DIRS.user_config_dir,
                'data': DEFAULT_DIRS.user_data_dir,
                'log': DEFAULT_DIRS.user_log_dir,
                'temp': DEFAULT_DIRS.user_temp_dir
                },
        'files': {
                'config': {
                        'core': DEFAULT_DIRS.user_config_dir.joinpath('config.ini'),
                        'logger': DEFAULT_DIRS.user_config_dir.joinpath('logger_config.ini'),
                        'developer_mode': DEFAULT_DIRS.user_config_dir.joinpath('developer_mode_config.ini'),
                        'alternate_dirs': DEFAULT_DIRS.user_config_dir.joinpath('alternate_dirs_config.ini'),
                        },
                'cache': DEFAULT_DIRS.user_cache_dir.joinpath('cache.ini'),

                },
        }


CONFIG_SYSTEM_MAP['logger']['default_config_filepath'] = FILE_SYSTEM_DEFAULTS['files']['config']['logger']
CONFIG_SYSTEM_MAP['developer_mode']['default_config_filepath'] = FILE_SYSTEM_DEFAULTS['files']['config']['developer_mode']
CONFIG_SYSTEM_MAP['alternate_dirs']['default_config_filepath'] = FILE_SYSTEM_DEFAULTS['files']['config']['alternate_dirs']


__all__ = [
    'CONFIG_SPECS',
    'CONFIG_SYSTEM_NAMES',
    'SPEC_FILE_PATHS'
]

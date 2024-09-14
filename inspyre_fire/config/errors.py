from inspyre_fire.errors import InspyreFireError


class ConfigError(InspyreFireError):
    """
    Base class for errors raised by the Config package.
    """
    __base_message = 'An error occurred in the Config package.'
    __info_unavailable = 'No additional information is available.'

    def __init__(self, message=None, code=0, **kwargs):
        self.__info_collection = []
        self._additional_info = message if message is not None else self.__info_unavailable
        self.__code = code
        self.__message = self.build_message()
        super().__init__(self.__message, self.__code, **kwargs)

    @property
    def additional_info(self):
        """Returns additional information about the error."""
        return self._additional_info

    @additional_info.setter
    def additional_info(self, new_info):
        """Sets additional information about the error."""
        self.__info_collection.append(new_info)

    @property
    def code(self):
        """Returns the error code."""
        return self.__code

    @property
    def info_collection(self):
        """Returns the collection of additional information."""
        return self.__info_collection

    def build_message(self):
        """Constructs the full error message."""
        return f'{self.__base_message}\n\n{(" " * 4)}{self.__class__.__name__}'


class InvalidConfigSystemError(ConfigError):
    """
    Raised when an invalid configuration system is provided.
    """

    def __init__(self, system=None, valid_systems: list = None):
        self._additional_info = 'Invalid configuration system provided.'

        if system:
            self._additional_info += f'\nSystem: {system}'

        if valid_systems:
            self._additional_info += f'\nValid Systems: {valid_systems}'

        self._line_number = self.get_line_number()
        self._file_raised = self.get_file_raised()

        super().__init__(self._additional_info)

    @property
    def line_number(self):
        return self._line_number

    @property
    def file_raised(self):
        return self._file_raised

    def __str__(self):
        return f'InvalidConfigSystemError: {self._additional_info}'


class ConfigDirectoryNonExistentError(ConfigError):
    """
    Raised when the configuration directory does not exist.
    """

    def __init__(self, directory=None):
        self._additional_info = 'Configuration directory does not exist.'

        if directory:
            self._additional_info += f'\nDirectory: {directory}'

        self._line_number = self.get_line_number()
        self._file_raised = self.get_file_raised()

        super().__init__(self._additional_info)

    @property
    def line_number(self):
        return self._line_number

    @property
    def file_raised(self):
        return self._file_raised

    def __str__(self):
        return f'ConfigDirectoryNonExistentError: {self._additional_info}'


class ConfigBackupDirectoryNonExistentError(ConfigError):
    """
    Raised when the configuration backup directory does not exist.
    """

    def __init__(self, directory=None):
        self._additional_info = 'Configuration backup directory does not exist.'

        if directory:
            self._additional_info += f'\nDirectory: {directory}'

        self._line_number = self.get_line_number()
        self._file_raised = self.get_file_raised()

        super().__init__(self._additional_info)

    @property
    def line_number(self):
        return self._line_number

    @property
    def file_raised(self):
        return self._file_raised

    def __str__(self):
        return f'ConfigBackupDirectoryNonExistentError: {self._additional_info}'

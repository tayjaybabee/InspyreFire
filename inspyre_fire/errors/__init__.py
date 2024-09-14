from inspyre_fire.errors.rich import RichRenderableError


class InspyreFireError(RichRenderableError):
    """
    Base class for errors raised by the Inspyre-Fire package.
    """
    __base_message = 'An error occurred in the Inspyre-Fire package.'
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


__all__ = [
    'InspyreFireError'
]

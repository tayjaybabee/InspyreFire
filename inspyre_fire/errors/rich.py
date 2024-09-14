import traceback
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


class RichRenderableError(Exception):
    """
    Base class for errors that can be rendered using the Rich library. This class provides a common method to render
    exceptions in a visually appealing way.
    """

    DIVIDER_OPTS = {
            'text':  f'\n{"-" * 30}\n',
            'style': 'bold green'
            }
    DIVIDER_PAIR = (DIVIDER_OPTS['text'], DIVIDER_OPTS['style'])
    SECTION_DIVIDER = Text(*DIVIDER_PAIR)

    @property
    def auto_rendered(self):
        return not self.__skipped_render

    @property
    def file_raised(self):
        return self.get_file_raised()

    @property
    def line_number(self):
        return self.get_line_number()

    @property
    def rendered(self):
        return self.__rendered

    def find_frame(self):
        tb = traceback.extract_stack()
        for frame in reversed(tb):
            if 'errors' not in frame.filename:
                return frame
        return None

    def get_file_raised(self):
        if frame := self.find_frame():
            return frame.filename

    def get_line_number(self):
        if frame := self.find_frame():
            return frame.lineno

    def __init__(
            self,
            message: str = None,
            code: int = 0,
            skip_render = False
            ):
        self.__rendered = False  # Flag to track if the error has been rendered
        self.__skipped_render = None
        super().__init__(message or 'An error occurred')

        if not skip_render:
            self.__skipped_render = False
            self.render()
        else:
            self.__skipped_render = True

    def build_additional_info(self):
        """
        Builds the additional information to be displayed with the error.
        """
        message = None
        if hasattr(self, 'info_collection') and len(self.info_collection) > 0:
            for info in self.info_collection:
                message += f'    - {info}\n'

        return message or self.additional_info

    def get_additional_renderable(self):
        line_number, file_name = self.line_number, self.file_raised
        assembled = [
                self.SECTION_DIVIDER,
                Text('\nAdditional Information:\n', 'italic cyan'),
                Text(f'\n    {self.build_additional_info()}\n', 'yellow'),
                self.SECTION_DIVIDER,
                Text('Error Information:', 'italic cyan'),
                Text(f'\n    File Raised: {file_name}', 'yellow'),
                Text(f'\n    Line Number: {line_number}', 'yellow'),
                ]

        return assembled

    def render(self, override_spent_status=False):
        """
        Render the exception using the Rich library.
        """
        if self.rendered and not override_spent_status:
            return

        console = Console()
        console.print(self)
        self.__rendered = True

    def __rich_console__(self, console: Console, options: dict):
        error_title = Text(f"Exception Raised: {self.__class__.__name__}", style="bold red")
        text = [
                Text(f'Message: \n    {self.args[0]}\n', style="bold white"),
                ]

        if hasattr(self, 'additional_info'):
            text.extend(self.get_additional_renderable())

        # You can customize the Panel appearance here
        panel = Panel(Text.assemble(*text), title=error_title, border_style="bright_red", expand=False)

        yield panel

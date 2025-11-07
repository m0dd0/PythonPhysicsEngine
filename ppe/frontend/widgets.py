class 

from ppe.utils.controllers import InputState # This is our generic interface, so it's fine

class AbstractUIElement(ABC):
    """
    An abstract, backend-agnostic base class for all UI elements.

    It defines the element's state and behavior using generic types,
    allowing concrete implementations for different rendering backends.
    """

    def __init__(self, x: int, y: int, width: int, height: int):
        """
        Initializes the UI element with its screen-space position and dimensions.

        Args:
            x: The screen-space x-coordinate of the top-left corner.
            y: The screen-space y-coordinate of the top-left corner.
            width: The width of the element in pixels.
            height: The height of the element in pixels.
        """
        # Store generic, primitive state
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        self.is_visible = True
        self.is_enabled = True

    @abstractmethod
    def update(self, input_state: InputState) -> None:
        """
        Processes user input and updates the element's internal state.

        Args:
            input_state (InputState): The current input state for the frame.
        """
        raise NotImplementedError

    @abstractmethod
    def draw(self, surface) -> None:
        """
        Draws the element to the screen.

        Args:
            surface: The rendering surface/context of the specific backend
                     (e.g., a pygame.Surface, an HTML5 canvas context, etc.).
        """
        raise NotImplementedError
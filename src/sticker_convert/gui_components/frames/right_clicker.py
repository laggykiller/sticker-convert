from ttkbootstrap import Menu # type: ignore
from tkinter import Event

# Reference: https://stackoverflow.com/a/57704013
class RightClicker:
    def __init__(self, event: Event):
        right_click_menu = Menu(None, tearoff=0, takefocus=0)

        for txt in ['Cut', 'Copy', 'Paste']:
            right_click_menu.add_command(
                label=txt, command=lambda event=event, text=txt:
                self.right_click_command(event, text))

        right_click_menu.tk_popup(event.x_root, event.y_root, entry='0')

    def right_click_command(self, event: Event, cmd: str):
        event.widget.event_generate(f'<<{cmd}>>')
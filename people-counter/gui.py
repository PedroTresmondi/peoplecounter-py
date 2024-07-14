import globals

def pause_video():
    globals.paused = not globals.paused

def set_entry_shape():
    globals.drawing_entry = True

def set_exit_shape():
    globals.drawing_entry = False

def set_drawing_mode_line():
    globals.drawing_mode = 'line'

def set_drawing_mode_yellow_line():
    globals.drawing_mode = 'yellow_line'

import queue

import PySimpleGUI as sg

import layout

# jenkins_base_url = 'https://builds.apache.org/'
from layout import TheGui
from worker import Worker

jenkins_base_url = 'https://qa.coreboot.org/'


def main():
    sg.theme('DarkAmber')   # Add a touch of color
    # All the stuff inside your window.

    gui_queue = queue.Queue()
    worker_queue = queue.Queue()
    the_gui = TheGui(jenkins_base_url, worker_queue)
    jserver = Worker(jenkins_base_url, gui_queue, worker_queue)
    jserver.start()
    # window['version'].update(jserver.version)
    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        # sg.popup_animated(sg.DEFAULT_BASE64_LOADING_GIF, 'Loading', time_between_frames=100)
        event, values = the_gui.window.read(timeout=100)
        if event == sg.WIN_CLOSED or event == 'Cancel':  # if user closes window or clicks cancel
            break
        if values[0]:
            print('You entered ', values[0])
        if event != '__TIMEOUT__':
            the_gui.event(event, values)
        try:
            message = gui_queue.get_nowait()  # see if something has been posted to Queue
            the_gui.message(message)
        except queue.Empty:  # get_nowait() will get exception when Queue is empty
            pass

    the_gui.window.close()
    worker_queue.put(('close', {}))
    jserver.join()


if __name__ == '__main__':
    main()

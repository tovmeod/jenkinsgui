import logging
import queue
from copy import deepcopy

import PySimpleGUI as sg


class TreeData(sg.TreeData):
    def message(self, messagevalue: list):
        for item in messagevalue:
            _class = item.pop('_class')
            if _class == 'hudson.model.ListView':
                self.add_view(item)

    def add_view(self, item):
        name = item.pop('name')
        url = item.pop('url')
        self.Insert('', key=url, text=name, values=[])


class TheGui:
    def __init__(self, base_url: str, worker_queue: queue.Queue):
        self.worker_queue = worker_queue
        # The tab 1, 2, 3 layouts - what goes inside the tab
        tab1_layout = [[sg.Text('Tab 1')],
                       [sg.Text('Put your layout in here')],
                       [sg.Text('Input something'), sg.Input(size=(12, 1), key='-IN-TAB1-')]]

        tab2_layout = [[sg.Text('Tab 2')]]
        tab3_layout = [[sg.Text('Tab 3')]]
        tab4_layout = [[sg.Text('Tab 3')]]

        # The TabgGroup layout - it must contain only Tabs
        tab_group_layout = [[sg.Tab('Tab 1', tab1_layout, font='Courier 15', key='-TAB1-'),
                             sg.Tab('Tab 2', tab2_layout, visible=False, key='-TAB2-'),
                             sg.Tab('Tab 3', tab3_layout, key='-TAB3-'),
                             sg.Tab('Tab 4', tab4_layout, visible=False, key='-TAB4-'),
                             ]]

        tab_group = sg.TabGroup(tab_group_layout, enable_events=True, key='-TABGROUP-')
        self.treedata = TreeData()
        self.layout = [
            [sg.Text('Jenkins '), sg.Text('connecting ...', key='version')],
            [sg.Text('Enter something on Row 2'), sg.InputText()],
            [sg.Button('Ok'), sg.Button('Cancel')],
            [sg.Frame('Frame', [[]], key='-FRAMETABGROUP-')],
            # [sg.Tree(data=self.treedata,
            #          headings=['Size', ],
            #          auto_size_columns=True,
            #          num_rows=20,
            #          col0_width=40,
            #          key='tree',
            #          show_expanded=False,
            #          enable_events=True),
            #  ]
        ]
        # Create the Window
        self.window = sg.Window(base_url, self.layout, resizable=True)
        self.window.finalize()

    def event(self, event, values):
        if event == '-TABGROUP-':
            self.tab_selected(event, values)
        elif event in self.table_keys:
            self.table_selected(event, values)
        else:
            print(event)
            print(values)

    def worker_call(self, fn, **kwargs):
        self.worker_queue.put((fn, kwargs))

    def tab_selected(self, event, values):
        tabkey = values[event]
        tab = self.window[tabkey]
        tabname = tab.Title
        self.worker_call('get_jobs', view_name=tabname)

    def table_selected(self, event, values):
        tablekey = event
        selected = values[tablekey]
        if selected:
            selected = selected[0]
            table = self.window[tablekey]
            jobs = table.metadata
            job = jobs[selected]
            job_name = job['name']
            self.worker_call('get_job_info', job_name=job_name)

    def message(self, message):
        """Handle the message from the worker thread"""
        function_name, kwargs = message
        f = getattr(self, function_name)
        f(**kwargs)
        # if location == 'tree':
        #     self.treedata.message(value)
        #     value = self.treedata
        # self.window[location].update(value)

    def set_version(self, version):
        self.window['version'].update(version)

    def add_tabs(self, views):
        tab_group_layout = []
        self.table_keys = []
        for view in views:
            _class = view.pop('_class')
            if _class in ('hudson.model.ListView', 'hudson.model.AllView'):
                name = view.pop('name')
                url = view.pop('url')

                headings = ['Color', 'Name']
                data = [['Loading'] * len(headings)]
                table_key = f'-TABLE-{name}'
                table = sg.Table(values=data, headings=headings, max_col_width=25,
                                 # background_color='light blue',
                                 auto_size_columns=True,
                                 display_row_numbers=True,
                                 justification='right',
                                 num_rows=20,
                                 alternating_row_color='lightyellow',
                                 key=table_key,
                                 row_height=35,
                                 tooltip='This is a table',
                                 enable_events=True)

                tab_layout = [[table]]
                tab_group_layout.append(sg.Tab(name, tab_layout, font='Courier 15', key=url))
                self.table_keys.append(table_key)
            else:
                logging.error(f'Unknown class {_class}')
        tab_group_layout = [tab_group_layout]
        tab_group = sg.TabGroup(tab_group_layout, enable_events=True, key='-TABGROUP-')
        self.window.extend_layout(self.window['-FRAMETABGROUP-'], [[tab_group]])

    def add_jobs(self, view_name, jobs: dict):
        table = self.window[f'-TABLE-{view_name}']
        table.metadata = deepcopy(jobs)
        data = []
        for job in jobs:
            _class = job.pop('_class')
            if _class in ('hudson.model.FreeStyleProject', ):
                name = job.pop('name')
                url = job.pop('url')
                color = job.pop('color')
                fullname = job.pop('fullname')  # I don't know what to do with fullname
                row = [color, name]
                data.append(row)
            else:
                logging.error(f'Unknown class {_class}')
        table.update(data)

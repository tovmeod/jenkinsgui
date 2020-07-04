import queue
from threading import Thread

import jenkins


class Worker(Thread):
    def __init__(self, base_url, gui_queue, worker_queue):
        super().__init__(daemon=True)
        self.base_url = base_url
        self.gui_queue = gui_queue
        self.worker_queue = worker_queue
        # self.server = jenkins.Jenkins('https://ci.jenkins.io/', username='myuser', password='mypassword')
        # user = server.get_whoami()
        # print('Hello %s from Jenkins %s' % (user['fullName'], version))
        self.keep_running = True

    def run(self):
        self.server = jenkins.Jenkins(self.base_url)
        try:
            version = self.server.get_version()
            self.gui_call('set_version', version=version)
            views = self.server.get_views()
            self.gui_call('add_tabs', views=views)
        except Exception as e:
            self.gui_call('set_version', version=str(e))
        while self.keep_running:
            try:
                message = self.worker_queue.get_nowait()  # see if something has been posted to Queue
                function_name, kwargs = message
                f = getattr(self, function_name)
                f(**kwargs)
            except queue.Empty:  # get_nowait() will get exception when Queue is empty
                pass
        print('finished worker')

    def gui_call(self, fn, **kwargs):
        self.gui_queue.put((fn, kwargs))

    def close(self):
        self.keep_running = False

    def get_jobs(self, view_name):
        jobs = self.server.get_jobs(view_name=view_name)
        self.gui_call('add_jobs', view_name=view_name, jobs=jobs)

    def get_job_info(self, job_name):
        job_info = self.server.get_job_info(job_name)
        print(job_info)

import importlib
import unittest
from django.test import TransactionTestCase
from django_geosource_nodes import mixins
from django_geosource_nodes.celery import tasks, app
from celery import Celery
from celery.result import AsyncResult
from celery.contrib.testing.worker import start_worker


# celery = Celery('tasks')


# makina corpus partager communication apn presentation makina
# class Test_TestMixins(TransactionTestCase):
#     @classmethod
#     def setUpClass(cls):
#         super().setUpClass()
#         cls.celery_worker = start_worker(app)
#         cls.celery_worker.__enter__()

#     @classmethod
#     def tearDownClass(cls):
#         super().tearDownClass()
#         cls.celery_worker.__exit__(None, None, None)

#     def setUp(self):
#         super().setUp()
#         self.task = tasks.foo.delay("bar") # whatever your method and args are
#         self.results = self.task.get()

#     # @celery.task
#     # def task_example(x, y):
#     #     return x+y

#     def test_update(self):
#         celerycallmethodmixins = mixins.CeleryCallMethodsMixin()
#         celerycallmethodmixins.update_status(task=self.task)
        

# if __name__ == '__main__':
#     unittest.main()
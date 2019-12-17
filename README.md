[![Build Status](https://travis-ci.org/Terralego/django-geosource.svg?branch=master)](https://travis-ci.org/Terralego/django-geosource)
[![codecov](https://codecov.io/gh/Terralego/django-geosource/branch/master/graph/badge.svg)](https://codecov.io/gh/Terralego/django-geosource)
[![PyPi version](https://pypip.in/v/django-geosource/badge.png)](https://pypi.org/project/django-geosource/)

# Django GEOSource

This django application provide a Rest Framework API that allow to manage many geo data
sources and integrate that data wherever you need, like a Django model or any output
pipeline. Its provided with necessary celery jobs that do the job.

## Settings

You can define the setting `GEOSOURCE_MAX_TASK_RUNTIME` that allow to define the max run time of a task before it can be launched one more
time. It allow to prevent when a task is stuck and disallow launching one more.

## Configure and run Celery

You must define in your project settings the variables CELERY_BROKER_URL and CELERY_RESULT_BACKEND as specified in Celery documentation.

To run the celery worker:
`$ celery worker -A django_geosource -l info`

To run the celery beat worker that allow to synchronize periodically sources, launch this command:
`$ celery beat --scheduler django_geosource.celery.schedulers.GeosourceScheduler -A django_geosource -l info`

## Configure data destination
Now, you must set the callback methods that are used to insert data in your destination database.

If you use django-geostore, we provide a set of callback in the `geostore_callbacks` module, else you can define your
own callbacks.

### GEOSOURCE_LAYER_CALLBACK
The callback signature receive as first argument the SourceModel object, and must return your Layer object.
Example:
```python
def layer_callback(geosource):
    return Layer.objects.get_or_create(name=geosource.name)[0]
```

### GEOSOURCE_FEATURE_CALLBACK
This one, define a feature creation callback method.
Example:
```python
def feature_callback(geosource, layer, identifier, geometry, attributes):
    return Feature.objects.get_or_create(layer=layer, identifier=identifier, geom=geometry, properties=attributes)[0]
```

### GEOSOURCE_CLEAN_FEATURE_CALLBACK
This callback is called when the refresh is done, to clear old features that are not anymore present in the database.
It receives as parametter the geosource, layer and begin update date, so you can advise what to do depending of your
models.
Example:
```python
def clear_features(geosource, layer, begin_date):
    return layer.features.filter(updated_at__lt=begin_date).delete()
```

### GEOSOURCE_DELETE_LAYER_CALLBACK
This is called when a Source is deleted, so you are able to do what you want with the loaded content in database, when
the source doesn't exist anymore. It's executed before real deletion.
Example:
```python
def delete_layer(geosource, layer):
    if layer.features.count() > 0:
        layer.features.delete()
    return layer.delete()
```


## To start a dev instance

Define settings you wants in `test_geosource` django project.

```sh
docker-compose up
```

First start should failed as the database need to be initialized. Just launch
the same command twice.

Then initialize the database:

```sh
docker-compose run web /code/venv/bin/python3 /code/src/manage.py migrate
```

You can now edit your code. A django runserver is launched internally so the
this is an autoreload server.

You can access to the api on http://localhost:8000/api/


## Test and coverage

To run test suite, just launch:

```sh
docker-compose run web /code/venv/bin/python3 /code/src/manage.py test
```

To run test suite with coverage, execute this commande:

```sh
docker-compose run web /code/src/coverage.sh
```

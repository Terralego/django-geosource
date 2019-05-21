# Django GEOSource

This django application provide a Rest Framework API that allow to manage many geo data
sources and integrate that data wherever you need, like a Django model or any output
pipeline. Its provided with necessary celery jobs that do the job.


## Configure and run Celery

You must define in your project settings the variables CELERY_BROKER_URL and CELERY_RESULT_BACKEND as specified in Celery documentation.

To run the celery worker:
`$ celery worker -A django_geosource -l info`


## Configure data destination
Now, you must set the callback methods that are used to insert data in your destination database.

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
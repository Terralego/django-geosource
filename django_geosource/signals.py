from django.dispatch import Signal

refresh_data_done = Signal(providing_args=["layer"])

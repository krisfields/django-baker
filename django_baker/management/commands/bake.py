from __future__ import print_function

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ImproperlyConfigured
from django.apps import apps

from ...bakery import Baker


class Command(BaseCommand):
    args = "appname:modelname,modelname2,modelname3"
    help = ("Generates generic views (create, update, detail, list, and delete), urls, forms, and admin for model in an"
            "app.  Optionally can restrict which apps are generated on a per app basis.\n\nexample: python manage.py "
            "bake bread:Sesame,Pumpkernickel donut:Glazed,Chocolate")

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('apps_and_models', nargs='+')

    def handle(self, *args, **options):
        ingredients = self.parse_bake_options(options["apps_and_models"])
        baker = Baker()
        baker.bake(ingredients)

    def parse_bake_options(self, apps_and_models):
        """
            Parses command line options to determine what apps and models for those apps we should bake.
        """
        apps_and_models_to_bake = {}
        for app_and_model in apps_and_models:
            app_and_model_names = app_and_model.split(':')
            app_label = app_and_model_names[0]
            if len(app_and_model_names) == 2:
                selected_model_names = app_and_model_names[1].split(",")
            else:
                selected_model_names = None
            app, models = self.get_app_and_models(app_label, selected_model_names)
            apps_and_models_to_bake[app_label] = (models, app)
        return apps_and_models_to_bake

    def get_app_and_models(self, app_label, model_names):
        """
            Gets the app and models when given app_label and model names
        """
        try:
            app = apps.get_app_config(app_label)
        except:
            raise CommandError("%s is ImproperlyConfigured - did you remember to add %s to settings.INSTALLED_APPS?" %
                               (app_label, app_label))

        models = self.get_selected_models(app, model_names)
        return (app, models)

    def get_selected_models(self, app, model_names):
        """
            Returns the model for a given app.  If given model_names, returns those so long as the model names are
            actually models in the given app.
        """
        if model_names:
            try:
                return [app.get_model(model_name) for model_name in model_names]
            except:
                raise CommandError("One or more of the models you entered for %s are incorrect." % app_label)
        else:
            return app.get_models()

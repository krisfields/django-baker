============
Django Baker
============

Django Baker wants to help you get your projects up and running quickly.  Given one or more app names, s/he will automatically generate views, forms, urls, admin, and templates for all of the models in the models.py file.  All files are pep-8 compliant (with exception to the maximum line length rule, which I don't agree with).

Once you add a single urlpattern to your project's URLconf, you'll have a working list view, detail view, create view, update view, and delete view for each model in your app.

Optionally you may specify which models in an app to bake if you'd rather not generate files for all of them.

You can override any of the template files that are used in the 'baking' process in the same way that you would override any third party template.  Just create a django_baker folder inside your project's main templates directory and create a file with the same name as any of the 9 files you wish to override, which are: detail.html, create.html, update.html, list.html, delete.html, views, urls, forms, admin, base, __init__urls, __init__views.  Hopefully their names are self explanatory.

**********
Installing
**********

.. code-block:: python

    pip install django-baker

Add 'django_baker' to INSTALLED_APPS

*****
Usage
*****

Let's assume your project is called TastyTreats, and has two apps, one called bread and another called pastries.

.. code-block:: python

    python manage.py bake bread pastries

This will generate files for all of the models in both of the apps.  You can override this by passing in models for each app.  Let's assume your pastries app has the following models: Tart, Strudel, and Danish but you only want to bake tarts and danishes.

.. code-block:: python

    python manage.py bake bread pastries:Tart,Danish

Finally you simply need to add one or more urlpattern to your project's URLconf.

.. code-block:: python

    (r'^pastries/', include('pastries.urls')),

will result in the following url schema:

.. code-block:: html

    www.tastytreats.com/pastries/tarts
    www.tastytreats.com/pastries/danishes

alternatively you can create multiple urlpatterns to create shorter urls.

.. code-block:: python

    (r'^tarts/', include('pastries.urls.tart_urls')),
    (r'^danishes/', include('pastries.urls.danish_urls')),

will result in the following url schema:

.. code-block:: html

    www.tastytreats.com/tarts
    www.tastytreats.com/danishes


Views
=====

To keep things tidy, a views directory is created, and each model is given it's own views file (ie. tart_views.py).  An __init__ file is created that imports from each of the views files.  With the __init__ file in place, you can import from any of the individual views files the same way you would have before (ie. from bread.views import CornBreadCreateView).

For convenience, almost all of the CBV methods that can be overridden are stubbed out, ready to be altered as needed.  The methods are presented in the order in which they are called. I chose to leave a couple of methods out as I couldn't imagine any scenario in which I would want to override them.

Also for convenience and easy alteration, almost all of the attributes that you can set are listed.

Some other niceties:
--------------------
- *form_class* is set to a ModelForm that was added to your forms.py file
- *context_object_name* is set to the slugified model_name (ie. tarts for DetailView, UpdateView, and DeleteView, or tarts_list for the ListView)
- if your model has exactly one unique slug field, it's used as the *slug_field* and *slug_url_kwarg* attribute.
- *get_success_url* returns the url for the object's DetailView (for DeleteView, the ListView url is returned).

Templates
=========

The generated templates files are kept very minimal as there aren't usually a lot of commonalities in templates between projects.  Each extends a model base file (ie. tart_base.html) which in turn extends "base.html", which your project is assumed to have.  The model level base file is empty but nice to have if you wish to add any html specific to that model.

The ListView template lists each object, with links to view, update, or delete. There is also a link to create a new object.

The DetailView template lists the object with a link to update or delete, as well as a link back to the list view.

Both the CreateView and UpdateView templates display the model form with a link back to the ListView.

The DeleteView template has a simple confirm required button and a link back to the ListView.

Forms
=====

A ModelForm is created for each model, with many of the commonly set attributes listed for easy alteration. The *fields* attribute is set to each field in the model other than the id.

In addition, a few commonly changed methods are stubbed out, including a *clean_field_name* method for each field in the form.

Urls
====

A new urls directory is created, with each model getting it's own file (ie. tart_urls.py).  An __init__ file is created which adds urlpatterns that include each of the newly created urls files.  This allows you to choose whether to add routing to the app as a whole, or individually to each model (see usage above).

For DetailView, UpdateView, and DeleteView, if a model has exactly one unique slug field, that slug field will be used in the url.  Otherwise pk will be used.

For CreateView, UpdateView, and DeleteView, the login_required decorator has been added as the vast majority of the time these actions tend to require the user to be logged in.  In the future, I intend to make this optional.

Admin
=====

This is where I really had some fun.  For each model, a ModelAdmin is created that makes use of a model admin mixin that I wrote.  The goal of ExtendedModelAdminMixin is to make setting up a fully functional admin for each model (with intelligently chosen list_display, list_filter, and search_fields) a one liner.

The actual contents of the admin.py files generated are fairly small, since most of the magic is happening in the ExtendedModelAdminMixin.  Many of the attributes that you can set are listed so that you may easily alter them as needed.  I didn't include any of the methods you can override as there are too many and it would get way too cluttered.  There are a lot of useful ones though, which you can view here: https://docs.djangoproject.com/en/1.10/ref/contrib/admin/#modeladmin-methods

ExtendedModelAdminMixin sets defaults for the following:

list_select_related
-------------------

Defaults to all of the model's ForeignKey and OneToOneFields, including those where null=True.  This will usually decrease database queries and improve page load time.

You can override this by setting **list_all_select_related** to False.

list_display
------------

Defaults to all of the model's fields, in the order that they are listed in your models.py file, with the exception of the id field and any ManyToManyField.

You can override this by setting the *list_display* attribute or you may extend it by setting **extra_list_display** (defaults to an empty list), the contents of which will be appended to *list_display*, with any fields in both being displayed only once.

In addition, each URLField, ForeignKey, and OneToOneField will display as a link.  URLFields will link to their respective urls, while ForeignKey and OneToOneFields will link to their respective object's admin change pages.

You can ovverride this functionality by setting **link_url_fields** and/or **link_foreign_key_fields** to False.

list_filter
-----------

Defaults to any field where the choices attribute has been set, as well as any field with a field type matching a field type in the **list_by_fields** attribute (defaults to ['BooleanField', 'NullBooleanField', 'USStateField']), as well as any ForeignKey field where the number of related objects is less than the **max_related_objects** attribute (defaults to 100).

You can override this by setting the *list_filter* attribute or you may extend it by setting **extra_list_filter** (defaults to an empty list), the contents of which will be appended to *list_filter*.

search_fields
-------------

Defaults to any field with a field type matching a field type in **search_by_fields** (defaults to ["CharField", "TextField"]),

You can override this by setting the *search_fields* attribute or you may extend it by setting **extra_search_fields** (defaults to an empty list), the contents of which will be appended to search_fields.

****
Note
****

Django Baker will remove 2 files (views.py, urls.py) from each app baked so long as the files are 4 lines or less (the initial size of the files when you run startapp).  This is necessary so they don't conflict with the newly generated views and urls folders.  If the files are greater than 4 lines you will need to remove them yourself.

**************************
The future of Django Baker
**************************

My top 3 todo items are:

1. Allow apps to be baked more than once to account for newly added models.  Right now the default behavior is to only create new files and skip any steps where the file about to be baked already exists.
2. Automatically generate tests for each app and model
3. Add tests to Django Baker itself
   
Pull requests are awesome.


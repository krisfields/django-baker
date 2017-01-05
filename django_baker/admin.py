from django.core.validators import URLValidator
from django.db.models.fields import FieldDoesNotExist
from django.utils.encoding import smart_text

from functools import partial


def number_field_choices(field):
    """
        Given a field, returns the number of choices.
    """
    try:
        return len(field.get_flat_choices())
    except AttributeError:
        return 0


def remove_dupes(seq, idfun=None):
    """
        Efficient method to remove dupes from list, while preserving order.
    """
    if idfun is None:
        def idfun(x):
            return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def is_urlfield(field, model=None):
    """
        Given a field, will check if it's a URLField or not.
        If model is given, field is actually a field_name and field must first be retrieved.
    """
    if model:
        try:
            field = model._meta.get_field(field)
        except FieldDoesNotExist:
            return False
    try:
        return field.default_validators[0].regex == URLValidator.regex
    except AttributeError:
        return False
    except IndexError:
        return False


def is_foreignkey(field_name, model):
    """
        Given a field_name and model, checks if field is ForeignKey or OneToOneField or not.
    """
    try:
        field = model._meta.get_field(field_name)
        if field.get_internal_type() in ["ForeignKey", "OneToOneField"]:
            return True
        return False
    except FieldDoesNotExist:
        return False


class ExtendedModelAdminMixin(object):
    """
        Model Admin Mixin that makes (hopefully) intelligent choices to minimize the time it takes to get the admin up
        and running.
    """
    extra_list_display = []
    extra_list_filter = []
    extra_search_fields = []
    link_url_fields = True
    link_foreign_key_fields = True
    max_related_objects = 100
    list_all_select_related = True
    filter_by_fields = ["BooleanField", "NullBooleanField", "USStateField"]
    search_by_fields = ["CharField", "TextField"]

    def __getattr__(cls, name):
        """
            Dynamically creates a new method for each URLField and ForeignKey/OneToOneField field that will return the
            object name with a link to either the webpage (if URLField) or admin change page
            (if ForeignKey/OneToOneField).
        """
        def url_link(instance, field):
            target = getattr(instance, field)
            if not target:
                return ""
            return '<a href="%s">%s</a>' % (target, target)

        def foreign_key_link(instance, field):
            target = getattr(instance, field)
            if not target:
                return "None"
            return u'<a href="../../%s/%s/%d">%s</a>' % (
                target._meta.app_label, target._meta.model_name, target.id, smart_text(target))

        if name[:9] == 'url_link_':
            method = partial(url_link, field=name[9:])
            method.__name__ = name[9:]
            method.allow_tags = True
            method.admin_order_field = name[9:]
            setattr(cls, name, method)
            return getattr(cls, name)

        if name[:8] == 'fk_link_':
            method = partial(foreign_key_link, field=name[8:])
            method.__name__ = name[8:]
            method.allow_tags = True
            setattr(cls, name, method)
            return getattr(cls, name)
        raise AttributeError

    def __init__(self, request, *args, **kwargs):
        """
            Sets list_all_select_related to all ForeignKey and OneToOneField fields which will cause queryset to
            select all of those fields, minimizing db queries.  Can be overridden by setting list_all_select_related to
            False.
        """
        super(ExtendedModelAdminMixin, self).__init__(request, *args, **kwargs)
        if self.list_all_select_related is True:
            self.list_select_related = [field.name for field in self.model._meta.fields if field.get_internal_type() in
                                        ["ForeignKey", "OneToOneField"]]

    def get_list_display(self, request):
        """
            Automatically creates admin list display for each field other than id.  Any fields in the extra_list_display
            attribute are added at the end of list_display.  Dupes are removed.
            URLField fields are created with links to the URL so long as the field is not in list_display_links.
            ForeignKey and OneToOneField fields are created with links to their admin change pages so long as the field
            is not in list_display_links.
        """
        list_display = super(ExtendedModelAdminMixin, self).get_list_display(request)
        if not isinstance(list_display, list):
            combined_list_display = ([field.name for field in self.model._meta.fields if field.name != "id"] +
                                     self.extra_list_display)
            list_display = remove_dupes(combined_list_display)
            if self.link_url_fields:
                list_display = ["url_link_%s" % field_name if is_urlfield(field_name, self.model) else field_name for
                                field_name in list_display]
            if self.link_foreign_key_fields:
                list_display = ["fk_link_%s" % field_name if is_foreignkey(field_name, self.model) else field_name for
                                field_name in list_display]
        list_display_links = self.get_list_display_links(request, list_display)
        list_display = [field_name.replace("url_link_", "").replace("fk_link_", "") if field_name in
                        list_display_links else field_name for field_name in list_display]
        return list_display

    def get_list_filter(self, request):
        """
            Automatically creates admin filters for every field listed in filter_by_fields attribute (defaults to
            BooleanField, NullBooleanField, USStateField, as well as any field with choices (ex. IntegerField with
            choices=SOMETHING) and any ForeignKey where the total number of objects is less than or equal to the
            max_related_objects attribute, which defaults to 100.
            Any fields in the extra_list_filter attribute are added at the end of list_filter.
        """
        list_filter = super(ExtendedModelAdminMixin, self).get_list_filter(request)
        if not isinstance(list_filter, list):
            combined_list_filter = ([field.name for field in self.model._meta.fields if
                                     (field.get_internal_type() in self.filter_by_fields) or
                                     (number_field_choices(field) > 0) or
                                     (field.get_internal_type() == "ForeignKey" and
                                      field.rel.to.objects.count() <= self.max_related_objects)] +
                                    self.extra_list_filter
                                    )
            list_filter = remove_dupes(combined_list_filter)
        return list_filter

    def get_search_fields(self, request):
        """
            Automatically creates admin search fields for every field listed in search_by_fields.
            Any fields in the extra_search_fields attribute are added at the end of search_fields.
        """
        search_fields = super(ExtendedModelAdminMixin, self).get_search_fields(request)
        if not isinstance(self.search_fields, list):
            combined_search_fields = ([field.name for field in self.model._meta.fields if field.get_internal_type() in
                                       self.search_by_fields] +
                                      self.extra_search_fields
                                      )
            search_fields = remove_dupes(combined_search_fields)
        return search_fields

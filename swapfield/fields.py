from django.db import models
from django.db.models import Max
from django.db.models.signals import post_save, pre_save
from django.core.exceptions import ValidationError


def _init_swap_integers(instance):
    if not hasattr(instance, 'swap_integers'):
        instance.swap_integers = {}


def _set_swap_integers(instance, predecessor, swap_value, column):
    _init_swap_integers(instance)
    predecessor_key = 'instance_{key}'.format(key=predecessor.pk)
    if predecessor_key not in instance.swap_integers:
        instance.swap_integers[predecessor_key] = {
            'value_predecessor': predecessor,
            'columns': {}
        }
    instance.swap_integers[predecessor_key]['columns'][column] = swap_value


class SwapIntegerField(models.IntegerField):

    def __init__(self, **kwargs):
        unique_for_fields = kwargs.get('unique_for_fields')
        # if 'null' not in kwargs or kwargs.get('null') is not True:
        #     raise TypeError("{class_name} must allow null values.".format(class_name=self.__class__.__name__))
        if 'unique' in kwargs:
            raise TypeError("{class_name} can't have a unique constraint.".format(class_name=self.__class__.__name__))
        if not isinstance(unique_for_fields, list):
            raise TypeError("{class_name} doesn't have a unique_for_fields (dict) param."
                            .format(class_name=self.__class__.__name__))
        self.unique_for_fields = unique_for_fields
        if 'unique_for_fields' in kwargs:
            del kwargs['unique_for_fields']
        super(SwapIntegerField, self).__init__(**kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(SwapIntegerField, self).deconstruct()
        if self.unique_for_fields:
            kwargs['unique_for_fields'] = self.unique_for_fields
        return name, path, args, kwargs

    def contribute_to_class(self, cls, name, *args, **kwargs):
        super(SwapIntegerField, self).contribute_to_class(cls, name)
        for constraint in cls._meta.unique_together:
            if self.name in constraint:
                raise TypeError("%s can't be part of a unique constraint." % self.__class__.__name__)
        pre_save.connect(self.get_swap_objects, sender=cls)
        post_save.connect(self.save_swap_objects, sender=cls)

    def save_swap_objects(self, sender, instance, created, **kwargs):
        swap_integers = getattr(instance, 'swap_integers', None)
        if swap_integers:
            for x in swap_integers:
                current_predecessor = swap_integers.get(x)
                value_predecessor = current_predecessor.get('value_predecessor')
                columns = current_predecessor.get('columns')
                for column in columns:
                    setattr(value_predecessor, column, columns.get(column))
                value_predecessor.save()

    def get_swap_objects(self, sender, instance, **kwargs):
        column = self.column
        new_value = getattr(instance, column)
        if new_value:
            # We need the value of field saved in database or the next available
            #  to swap with the object that contains the new value.
            swap_value = self._get_swap_value(instance)
            if swap_value and new_value != swap_value:
                predecessor = self._get_predecessor(instance, new_value)
                if predecessor:
                    _set_swap_integers(instance, predecessor, swap_value, column)

    def _get_swap_value(self, instance):
        swap_value = self._get_old_value(instance)  # TODO Maybe exists best method to get this value
        if not swap_value:
            swap_value = self._get_next_available_value(instance)
        # if not exists neither old_value nor next_available, assume this is the first record and
        # behaves the same than integer field
        return swap_value

    def _get_old_value(self, instance):
        if instance.pk:
            old_instance = self.model.objects.filter(pk=instance.pk).first()
            return getattr(old_instance, self.column) if old_instance else None
        return None

    def _get_common_filter(self, instance):
        query_filter = {}
        for field in self.unique_for_fields:
            query_filter[field] = getattr(instance, field)
        return query_filter

    def _get_first_available_value(self, instance):
        raise NotImplementedError('Not implemented yet')

    def _get_next_available_value(self, instance):
        query_filter = self._get_common_filter(instance)
        queryset = self.model.objects.filter(**query_filter)
        if queryset.count():
            aggregate = queryset.aggregate(value__max=Max(self.column))
            value_max = aggregate.get('value__max')
            return value_max + 1 if value_max else None
        return None

    def _get_predecessor(self, instance, data):
        query_filter = self._get_common_filter(instance)
        query_filter[self.column] = data

        queryset = self.model.objects.filter(**query_filter)
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.count() > 1:
            raise ValidationError(
                {self.column: 'Value {data} is repeated many times. Fix it.'.format(data=data)}
            )
        return queryset.first()


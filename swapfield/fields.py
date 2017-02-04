from django.db import models
from django.db.models.signals import post_save, pre_save
from django.core.exceptions import ValidationError


def _init_swap_integers(instance):
    if not hasattr(instance, 'swap_integers'):
        instance.swap_integers = []


class SwapIntegerField(models.IntegerField):

    def __init__(self, **kwargs):
        unique_for_fields = kwargs.get('unique_for_fields')
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
                value_predecessor = x.get('value_predecessor')
                setattr(value_predecessor, x.get('column'), x.get('new_value'))
                value_predecessor.save()

    def get_swap_objects(self, sender, instance, **kwargs):
        column = self.column
        # We need the value of field saved in database to swap with the object that contains the new value.

        old_value = self.get_old_value(instance)  # TODO Maybe exists best method to get this value
        new_value = getattr(instance, column)
        if new_value != old_value:
            predecessor = self.get_predecessor(instance, new_value)
            if predecessor:
                _init_swap_integers(instance)
                instance.swap_integers.append(
                    {'value_predecessor': predecessor, 'new_value': old_value, 'column': column}
                )

    def get_old_value(self, instance):
        if instance.pk:
            old_instance = self.model.objects.filter(pk=instance.pk).first()
            return getattr(old_instance, self.column)
        return None

    def get_predecessor(self, instance, data):
        query_filter = {}
        for field in self.unique_for_fields:
            query_filter[field] = getattr(instance, field)
        query_filter[self.column] = data

        queryset = self.model.objects.filter(**query_filter)
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        if queryset.count() > 1:
            raise ValidationError(
                {self.column: 'Value {data} is repeated many times. Fix it.'.format(data=data)}
            )
        return queryset.first()


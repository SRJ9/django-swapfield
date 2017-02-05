[![Build
Status](https://travis-ci.org/SRJ9/django-swapfield.svg?branch=master)](https://travis-ci.org/SRJ9/django-swapfield)
# django-swapfield
Easy! When you use django-swapfield if the value is saved in other record, values are swapped! You can configure what 
conditions must be repeated in both records to make the change.

How to
======
~~~~ {.sourceCode .bash}
$ pip install django-swapfield
$ # Define a SwapIntegerField in your model with unique_for_fields param (fields coincidence to can swap values)
$ # That SwapIntegerField can't be a part of unique_together or unique restriction.
~~~~

Uses e.g.
========
* Uniform number in sport team.
* Race number in an athletic competition.
* Any scenario when you want to swap values without reordering.

example
=======
~~~~ {.sourceCode .bash}
from swapfield.fields import SwapIntegerField

class Player(models.Model):
    name = models.CharField(max_length=30)
    team = models.ForeignKey(Team)
    number = SwapIntegerField(unique_for_fields=['team'])
    # can swap "number" if "team" has the same value
~~~~

Available fields
================
* SwapIntegerField

Method
======
* Current status allow swap values if not exists unique/unique_together restriction. First, get the registry (if exists)
what contains the new value to assign it the old value from registry what currently is saving. When current registry is
saved, replace the other registry with old value.
* In next versions, other method will be used when exists unique/unique_together restriction.

to-do list
==========
- [ ] Two or more django-swapfield in the same object.
- [ ] Alternative method when exists unique/unique_together restriction
- [ ] Friendly validation error with Django Admin (no Fatal error)
- [ ] Abstract django-swap-field
- [ ] SwapCharField
- [x] Tests for functionality
- [ ] Tests for migrations
- [ ] Config setting to choose swap value when a new record (not edited) get a value that exists in database: choose the
max value +1 or the first available.
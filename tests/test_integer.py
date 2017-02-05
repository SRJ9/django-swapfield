# -*- coding: utf-8 -*-
from django.test import TestCase

from tests.testapp.models import Team, Player


class SwapTestCase(TestCase):
    def setUp(self):
        Team.objects.create(name='Team A')
        Team.objects.create(name='Team B')

    def test_swap_integer(self):
        team_a = Team.objects.get(name='Team A')
        Player.objects.create(name='Player A', team=team_a, number=1)
        Player.objects.create(name='Player B', team=team_a, number=8)
        Player.objects.create(name='Player C', team=team_a, number=25)

        player_a = Player.objects.get(name='Player A')
        player_a.number = 8
        player_a.save()

        # player b number must be 1
        player_b = Player.objects.get(name='Player B')
        self.assertEqual(player_b.number, 1)

        Player.objects.create(name='Player D', team=team_a, number=25)

        # Player D get number 25, Player C will get the next available (26)
        player_c = Player.objects.get(name='Player C')
        self.assertEqual(player_c.number, 26)

        # TODO Config setting to choose swap value when a new record (not edited) get a value that exists in database
        # Value in predecessor record can be:
        # - The next available (current behavior): max value + 1
        # - The first available: [1, 8, 25, 26] --> 2 is the first available.

# -*- coding: utf-8 -*-
from django.test import TestCase
from .project.testapp.models import Team, Player


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

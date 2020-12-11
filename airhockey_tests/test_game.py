import unittest
from airhockey.game import World, PuckInfo


class TestWorld(unittest.TestCase):
    def assert_intersection(self, expected, actual):
        e_point, e_eta = expected
        a_point, a_eta = actual

        self.assertEqual(e_point, a_point)
        self.assertAlmostEqual(e_eta, a_eta, 3)

    def test_intersect_puck_trajectory_at_x_1(self):
        """
            Puck moves in parallel to the table edges towards the robot 
        """
        w = World(table_size=(1200, 600))
        w.puck_info = PuckInfo(position=(600, 300), vector=(-1, 0), velocity=100)

        intersection = w.intersect_puck_trajectory_at_x(0)
        self.assert_intersection(((0.0, 300.0), 6.0), intersection)

        intersection = w.intersect_puck_trajectory_at_x(100)
        self.assert_intersection(((100.0, 300.0), 5.0), intersection)

    def test_intersect_puck_trajectory_at_x_2(self):
        """
            Puck moves at 45 degrees 
        """
        w = World(table_size=(1200, 600))

        w.puck_info = PuckInfo(position=(600, 300), vector=(-1, -1), velocity=100)
        intersection = w.intersect_puck_trajectory_at_x(0)
        self.assert_intersection(((0.0, 300.0), 8.485), intersection)

        w.puck_info = PuckInfo(position=(600, 300), vector=(-1, 1), velocity=100)
        intersection = w.intersect_puck_trajectory_at_x(0)
        self.assert_intersection(((0.0, 300.0), 8.485), intersection)

    def test_multiple_edge_hits(self):
        w = World(table_size=(1200, 600))

        w.puck_info = PuckInfo(position=(600, 300), vector=(-1.5, -3), velocity=100)

        intersection = w.intersect_puck_trajectory_at_x(0)
        self.assert_intersection(((0.0, 300.0), 13.416), intersection)

        intersection = w.intersect_puck_trajectory_at_x(150)
        self.assert_intersection(((150.0, 600.0), 10.062), intersection)
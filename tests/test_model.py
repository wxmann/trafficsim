from unittest import TestCase

from trafficsim.model import VehicleState, Vehicle, Lane, World


class MockLane(Lane):
    def __init__(self):
        super(MockLane, self).__init__()

    def add(self, vehicle):
        pass

    def remove(self, vehicle):
        pass


mocklane = MockLane()

mockworld = World()


class TestVehicleState(TestCase):
    def test_should_coalesce_none_fields(self):
        state1 = VehicleState.undefined()
        state1.position = 1
        state1.speed = 2

        state2 = VehicleState(1, 3, 'lane')
        state1.coalesce(state2)

        self.assertEqual(state1.position, 1)
        self.assertEqual(state1.speed, 2)
        self.assertEqual(state1.lane, 'lane')


class TestVehicle(TestCase):
    def setUp(self):
        self.mockworld = mockworld
        self.mocklane = mocklane

    def test_get_speed_initialized_to_target_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        self.assertEqual(veh.speed, 10)

    def test_set_speed_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh.speed = 50
        veh.apply()
        self.assertEqual(veh.speed, 50)

    def test_get_position(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        self.assertEqual(veh.position, 5)

    def test_set_position_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh.position = 55
        veh.apply()
        self.assertEqual(veh.position, 55)

    def test_get_lane(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        self.assertEqual(veh.lane, self.mocklane)

    def test_set_lane_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        another_lane = MockLane()
        veh.lane = another_lane
        veh.apply()
        self.assertIs(veh.lane, another_lane)

    def test_calc_next_predicted_position_current_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh._current_state.speed = 15
        self.assertEqual(veh.next_predicted_position(), 20)

    def test_calc_next_predicted_position_set_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh.speed = 20
        self.assertEqual(veh.next_predicted_position(), 25)

    def test_cruise(self):
        veh = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh.cruise()
        veh.apply()
        self.assertEqual(veh.position, 15)

        veh.speed = 15
        veh.cruise()
        veh.apply()
        self.assertEqual(veh.position, 30)

    def test_can_change_lane(self):
        lane1, lane2 = Lane(), Lane()
        lane1.right = lane2
        lane2.left = lane1

        veh1_lane1 = Vehicle(10, 5, lane1, self.mockworld)
        veh2_lane1 = Vehicle(22, 4, lane1, self.mockworld)
        veh3_lane1 = Vehicle(99, 10, lane1, self.mockworld)
        lane1.add(veh1_lane1)
        lane1.add(veh2_lane1)
        lane1.add(veh3_lane1)

        veh1_lane2 = Vehicle(11, 3, lane2, self.mockworld)
        veh2_lane2 = Vehicle(39, 7, lane2, self.mockworld)
        lane2.add(veh1_lane2)
        lane2.add(veh2_lane2)

        self.assertFalse(veh1_lane1._can_change_lane(lane2))
        self.assertFalse(veh1_lane2._can_change_lane(lane1))
        self.assertTrue(veh2_lane1._can_change_lane(lane2))
        self.assertTrue(veh2_lane2._can_change_lane(lane1))
        self.assertTrue(veh3_lane1._can_change_lane(lane2))


class LaneTest(TestCase):
    def setUp(self):
        self.dummyworld = mockworld

    def test_add_vehicle_to_lane(self):
        lane = Lane()
        veh = 'dummy_vehicle'
        lane.add(veh)

        self.assertIn(veh, lane)

    def test_remove_vehicle_from_lane(self):
        lane = Lane()
        veh = 'dummy_vehicle'
        lane.add(veh)
        lane.remove(veh)

        self.assertNotIn(veh, lane)

    def test_get_first_vehicle_ahead(self):
        lane = Lane()
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane, self.dummyworld) for pos in [1, 5, 6, 122])
        self.assertEqual(lane.first_vehicle_ahead(7), veh4)
        self.assertEqual(lane.first_vehicle_ahead(2), veh2)
        self.assertEqual(lane.first_vehicle_ahead(123), None)

    def test_get_first_vehicle_behind(self):
        lane = Lane()
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane, self.dummyworld) for pos in [1, 5, 6, 122])
        self.assertEqual(lane.first_vehicle_behind(7), veh3)
        self.assertEqual(lane.first_vehicle_behind(1), None)
        self.assertEqual(lane.first_vehicle_behind(123), veh4)
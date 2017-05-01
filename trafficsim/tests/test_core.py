from unittest import TestCase

from mock import MagicMock

from trafficsim.core import VehicleState, Vehicle, Lane, World, VEHICLE_LENGTH


def mocklane():
    return MagicMock(spec=Lane)


def mockworld():
    return MagicMock(spec=World)


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
        self.mockworld = mockworld()
        self.mocklane = mocklane()

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
        another_lane = mocklane()
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

    def test_eq(self):
        veh1 = Vehicle(position=5, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh2 = Vehicle(position=10, target_speed=10, lane=self.mocklane, world=self.mockworld)
        veh3 = Vehicle(position=10, target_speed=10, lane=self.mocklane, world=self.mockworld)

        self.assertEqual(veh2, veh3)
        self.assertNotEqual(veh1, veh2)
        self.assertNotEqual(veh1, veh3)

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
        lane1, lane2 = Lane(1), Lane(2)

        veh1_lane1 = Vehicle(10, 5, lane1, self.mockworld)
        veh2_lane1 = Vehicle(22, 4, lane1, self.mockworld)
        veh3_lane1 = Vehicle(99, 10, lane1, self.mockworld)

        veh1_lane2 = Vehicle(11, 3, lane2, self.mockworld)
        veh2_lane2 = Vehicle(39, 7, lane2, self.mockworld)

        self.assertFalse(veh1_lane1.can_change_lane(lane2))
        self.assertFalse(veh1_lane2.can_change_lane(lane1))
        self.assertTrue(veh2_lane1.can_change_lane(lane2))
        self.assertTrue(veh2_lane2.can_change_lane(lane1))
        self.assertTrue(veh3_lane1.can_change_lane(lane2))

    def test_change_lane_at_speed(self):
        lane1, lane2 = Lane(1), Lane(2)

        veh_lane1 = Vehicle(10, 5, lane1, self.mockworld)
        veh_lane1.change_lane(lane2, 7)
        veh_lane1.apply()

        self.assertIs(veh_lane1.lane, lane2)
        self.assertEqual(veh_lane1.speed, 7)

    def test_max_speed_on_current_lane(self):
        lane = Lane(1)
        veh1 = Vehicle(10, 5, lane, self.mockworld)
        veh2 = Vehicle(15, 1, lane, self.mockworld)
        veh3 = Vehicle(100, 5, lane, self.mockworld)

        self.assertAlmostEqual(veh1.max_speed_on(), 16 - VEHICLE_LENGTH - 10)
        self.assertEqual(veh2.max_speed_on(), 1)
        self.assertEqual(veh3.max_speed_on(), 5)

    def test_max_speed_on_different_lane(self):
        lane1 = Lane(1)
        lane2 = Lane(2)

        veh1 = Vehicle(10, 5, lane1, self.mockworld)
        veh2 = Vehicle(15, 1, lane2, self.mockworld)
        veh3 = Vehicle(100, 5, lane2, self.mockworld)

        self.assertAlmostEqual(veh1.max_speed_on(lane2), 16 - VEHICLE_LENGTH - 10)

    def test_calculate(self):
        realworld = World(numlanes=2)
        realworld.request_change = MagicMock()
        lane1, lane2 = realworld.lanes()

        veh1_lane1 = Vehicle(21, 5, lane1, realworld)
        veh2_lane1 = Vehicle(25, 4, lane1, realworld)
        veh3_lane1 = Vehicle(27, 3, lane1, realworld)
        veh4_lane1 = Vehicle(99, 6, lane1, realworld)

        veh1_lane2 = Vehicle(21, 3, lane2, realworld)

        # V4, L1 => cruises.
        veh4_lane1.calculate()
        realworld.request_change.assert_called_with(veh4_lane1, lane1, 6)

        # V3, L1 => cruises.
        veh3_lane1.calculate()
        realworld.request_change.assert_called_with(veh3_lane1, lane1, 3)

        # V2, L1 => switches lanes.
        veh2_lane1.calculate()
        realworld.request_change.assert_called_with(veh2_lane1, lane2, 4)

        # V1, L1 => must brake to maintain VEHICLE_LENGTH distance
        veh1_lane1.calculate()
        realworld.request_change.assert_called_with(veh1_lane1, lane1, 3.2)

        # V1, L2 => cruises.
        veh1_lane2.calculate()
        realworld.request_change.assert_called_with(veh1_lane2, lane2, 3)


class TestLane(TestCase):
    def setUp(self):
        self.dummyworld = mockworld()

    def test_add_vehicle_to_lane(self):
        lane = Lane(1)
        veh = 'dummy_vehicle'
        lane.add(veh)

        self.assertIn(veh, lane)

    def test_remove_vehicle_from_lane(self):
        lane = Lane(1)
        veh = 'dummy_vehicle'
        lane.add(veh)
        lane.remove(veh)

        self.assertNotIn(veh, lane)

    def test_get_first_vehicle_ahead(self):
        lane = Lane(1)
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane, self.dummyworld) for pos in [1, 5, 6, 122])
        self.assertEqual(lane.first_vehicle_ahead(7), veh4)
        self.assertEqual(lane.first_vehicle_ahead(2), veh2)
        self.assertEqual(lane.first_vehicle_ahead(123), None)

    def test_get_first_vehicle_behind(self):
        lane = Lane(1)
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane, self.dummyworld) for pos in [1, 5, 6, 122])
        self.assertEqual(lane.first_vehicle_behind(7), veh3)
        self.assertEqual(lane.first_vehicle_behind(1), None)
        self.assertEqual(lane.first_vehicle_behind(123), veh4)
from unittest import TestCase

from trafficsim.model import VehicleState, Vehicle, Lane


class TestVehicleState(TestCase):
    def test_should_coalesce_none_fields(self):
        state1 = VehicleState.undefined()
        state1.position = 1
        state1.speed = 2

        state2 = VehicleState(1, 3, 'lane', None, 'prev_vehicle')
        state1.coalesce(state2)

        self.assertEqual(state1.position, 1)
        self.assertEqual(state1.speed, 2)
        self.assertEqual(state1.lane, 'lane')
        self.assertEqual(state1.next_vehicle, None)
        self.assertEqual(state1.prev_vehicle, 'prev_vehicle')


class MockLane(Lane):
    def __init__(self):
        super(MockLane, self).__init__()

    def add(self, vehicle):
        pass

    def remove(self, vehicle):
        pass


class TestVehicle(TestCase):
    def test_get_speed_initialized_to_target_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        self.assertEqual(veh.speed, 10)

    def test_set_speed_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        veh.speed = 50
        veh.apply()
        self.assertEqual(veh.speed, 50)

    def test_get_position(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        self.assertEqual(veh.position, 5)

    def test_set_position_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        veh.position = 55
        veh.apply()
        self.assertEqual(veh.position, 55)

    def test_get_lane(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        self.assertEqual(veh.lane, 'dummy_lane')

    def test_set_lane_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane=MockLane())
        another_lane = MockLane()
        veh.lane = another_lane
        veh.apply()
        self.assertIs(veh.lane, another_lane)

    def test_get_vehicle_in_front(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane', next_vehicle='vehicle_in_front')
        self.assertEqual(veh.vehicle_in_front, 'vehicle_in_front')

    def test_set_vehicle_in_front_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane', next_vehicle='vehicle_in_front')
        veh.vehicle_in_front = 'vehicle_in_front2'
        veh.apply()
        self.assertEqual(veh.vehicle_in_front, 'vehicle_in_front2')

    def test_get_vehicle_behind(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane', prev_vehicle='vehicle_behind')
        self.assertEqual(veh.vehicle_behind, 'vehicle_behind')

    def test_set_vehicle_behind_and_apply(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane', prev_vehicle='vehicle_behind')
        veh.vehicle_behind = 'vehicle_behind2'
        veh.apply()
        self.assertEqual(veh.vehicle_behind, 'vehicle_behind2')

    def test_calc_next_predicted_position_current_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        veh._current_state.speed = 15
        self.assertEqual(veh.next_predicted_position(), 20)

    def test_calc_next_predicted_position_set_speed(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        veh.speed = 25
        self.assertEqual(veh.next_predicted_position(), 30)

    def test_calc_ideal_position(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
        self.assertEqual(veh.next_predicted_position(), 15)

    def test_cruise(self):
        veh = Vehicle(position=5, target_speed=10, lane='dummy_lane')
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

        veh1_lane1 = Vehicle(10, 5, lane1)
        veh2_lane1 = Vehicle(22, 4, lane1)
        veh3_lane1 = Vehicle(99, 10, lane1)
        veh1_lane1.set_vehicles(veh2_lane1, None)
        veh2_lane1.set_vehicles(veh3_lane1, veh1_lane1)
        lane1.add(veh1_lane1)
        lane1.add(veh2_lane1)
        lane1.add(veh3_lane1)

        veh1_lane2 = Vehicle(11, 3, lane2)
        veh2_lane2 = Vehicle(39, 7, lane2)
        veh1_lane2.set_vehicles(veh2_lane2, None)
        veh2_lane2.set_vehicles(None, veh1_lane2)
        lane2.add(veh1_lane2)
        lane2.add(veh2_lane2)

        self.assertFalse(veh1_lane1.can_change_lane(lane2))
        self.assertFalse(veh1_lane2.can_change_lane(lane1))
        self.assertTrue(veh2_lane1.can_change_lane(lane2))
        self.assertTrue(veh2_lane2.can_change_lane(lane1))
        self.assertTrue(veh3_lane1.can_change_lane(lane2))

    def test_change_lane(self):
        lane1, lane2 = Lane(), Lane()
        lane1.right = lane2
        lane2.left = lane1

        veh1_lane1 = Vehicle(10, 5, lane1)
        veh2_lane1 = Vehicle(22, 4, lane1)
        veh3_lane1 = Vehicle(99, 10, lane1, prev_vehicle=veh2_lane1)
        veh1_lane1.set_vehicles(veh2_lane1, None)
        veh2_lane1.set_vehicles(veh3_lane1, veh1_lane1)
        lane1.add(veh1_lane1)
        lane1.add(veh2_lane1)
        lane1.add(veh3_lane1)

        veh1_lane2 = Vehicle(11, 3, lane2)
        veh2_lane2 = Vehicle(39, 7, lane2)
        veh1_lane2.set_vehicles(veh2_lane2, None)
        veh2_lane2.set_vehicles(None, veh1_lane2)
        lane2.add(veh1_lane2)
        lane2.add(veh2_lane2)

        veh2_lane2.change_lane(lane1)
        veh3_lane1.change_lane(lane2)
        for veh in lane1:
            veh.apply()
        for veh in lane2:
            veh.apply()

        # check vehicles are in the right lane
        self.assertNotIn(veh2_lane2, lane2)
        self.assertIn(veh2_lane2, lane1)
        self.assertNotIn(veh3_lane1, lane1)
        self.assertIn(veh3_lane1, lane2)

        # check whether vehicles have right references to each other
        self.assertEqual(veh2_lane1.vehicle_in_front, veh2_lane2)
        self.assertEqual(veh2_lane2.vehicle_behind, veh2_lane1)
        self.assertIsNone(veh2_lane2.vehicle_in_front)


class LaneTest(TestCase):
    def test_add_vehicle_to_lane(self):
        lane = Lane()
        veh = Vehicle(position=5, target_speed=10, lane=lane)
        lane.add(veh)

        self.assertIn(veh, lane)

    def test_remove_vehicle_from_lane(self):
        lane = Lane()
        veh = Vehicle(position=5, target_speed=10, lane=lane)
        lane.add(veh)
        lane.remove(veh)

        self.assertNotIn(veh, lane)

    def test_get_first_vehicle_ahead(self):
        lane = Lane()
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane) for pos in [1, 5, 6, 122])
        for veh in veh1, veh2, veh3, veh4:
            lane.add(veh)
        self.assertEqual(lane.first_vehicle_ahead(7), veh4)
        self.assertEqual(lane.first_vehicle_ahead(2), veh2)
        self.assertEqual(lane.first_vehicle_ahead(123), None)

    def test_get_first_vehicle_behind(self):
        lane = Lane()
        veh1, veh2, veh3, veh4 = tuple(Vehicle(pos, 10, lane) for pos in [1, 5, 6, 122])
        for veh in veh1, veh2, veh3, veh4:
            lane.add(veh)
        self.assertEqual(lane.first_vehicle_behind(7), veh3)
        self.assertEqual(lane.first_vehicle_behind(1), None)
        self.assertEqual(lane.first_vehicle_behind(123), veh4)
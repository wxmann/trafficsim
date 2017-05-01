from collections import namedtuple
import itertools


VEHICLE_LENGTH = 4.8  # meters


class VehicleState(object):
    @classmethod
    def undefined(cls):
        return VehicleState(None, None, None)

    def __init__(self, position, speed, lane):
        self.position = position
        self.speed = speed
        self.lane = lane

    def coalesce(self, another_state):
        self.position = first_not_none(self.position, another_state.position)
        self.speed = first_not_none(self.speed, another_state.speed)
        self.lane = first_not_none(self.lane, another_state.lane)


def first_not_none(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


def has_conflict(veh1, veh2):
    if veh1 is None or veh2 is None:
        return False
    return abs(veh1.next_predicted_position() - veh2.next_predicted_position()) < VEHICLE_LENGTH


class Vehicle(object):
    def __init__(self, position, target_speed, lane, world):
        self.target_speed = target_speed
        self._current_state = VehicleState(position, target_speed, lane)
        self._next_state = VehicleState.undefined()
        self._world = world

        # register vehicle with lane and world.
        self._register()

    def _register(self):
        self.lane.add(self)

    @property
    def speed(self):
        return self._current_state.speed

    @speed.setter
    def speed(self, newspeed):
        self._next_state.speed = newspeed

    @property
    def position(self):
        return self._current_state.position

    @position.setter
    def position(self, newpos):
        self._next_state.position = newpos

    @property
    def lane(self):
        return self._current_state.lane

    @lane.setter
    def lane(self, newlane):
        self._next_state.lane = newlane

    def next_predicted_position(self):
        return self.position + first_not_none(self._next_state.speed, self.speed)

    def cruise(self, speed=None):
        if speed is not None:
            self.speed = speed
        self.position = self.next_predicted_position()

    def change_lane(self, lane, speed=None):
        if speed is not None:
            self.speed = speed
        self.lane = lane

    def calculate(self):
        next_lane, next_speed = self._decide_lane_and_speed()
        self._world.request_change(self, next_lane, next_speed)

    def _vehicles_around_position(self, lane):
        return lane.first_vehicle_ahead(self.position), lane.first_vehicle_behind(self.position)

    def can_change_lane(self, lane):
        if lane is None:
            return False

        if lane is self.lane:
            return True
        else:
            if lane.vehicle_on(self.position):
                return False
            lane_veh_ahead, lane_veh_behind = self._vehicles_around_position(lane)
            return not has_conflict(self, lane_veh_ahead) and not has_conflict(self, lane_veh_behind)

    def _decide_lane_and_speed(self):
        speed_lanes_map = {}
        for lane in self.lane, self._world.left_of(self.lane), self._world.right_of(self.lane):
            if self.can_change_lane(lane):
                speed_on_lane = self.max_speed_on(lane)
                if speed_on_lane not in speed_lanes_map:
                    speed_lanes_map[speed_on_lane] = []
                speed_lanes_map[speed_on_lane].append(lane)

        max_speed = max(speed_lanes_map)
        # our lane will take priority over left lane, which will in turn take priority over right lane
        return speed_lanes_map[max_speed][0], max_speed

    def max_speed_on(self, lane=None):
        if lane is None:
            lane = self.lane
        lane_veh_ahead, _ = self._vehicles_around_position(lane)
        if lane_veh_ahead is None:
            return self.target_speed
        else:
            v_threshold = lane_veh_ahead.next_predicted_position() - self.position - VEHICLE_LENGTH
            max_speed = min(v_threshold, self.target_speed)
            # This should never happen in our lane, but we might revisit this...
            if max_speed < 0 and lane is self.lane:
                raise VehicleAccident("Something is wrong with the simulation; calculated speed < 0 for our lane.")
            return max_speed

    def apply(self):
        self._next_state.coalesce(self._current_state)
        self._track_lanes(self._next_state.lane)
        self._current_state = self._next_state
        self._next_state = VehicleState.undefined()

    def _track_lanes(self, new_lane):
        if new_lane is not self.lane:
            original_lane = self.lane
            original_lane.remove(self)
            new_lane.add(self)

    def __eq__(self, other):
        if self is other:
            return True
        if not isinstance(other, Vehicle):
            return False
        return self.position == other.position and self.lane is other.lane

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return id(self)


class VehicleAccident(Exception):
    pass


class Lane(object):
    def __init__(self, lane_number):
        self.lane_number = lane_number
        self._vehicles = []

    def add(self, vehicle):
        self._vehicles.append(vehicle)

    def remove(self, vehicle):
        try:
            self._vehicles.remove(vehicle)
        except ValueError:
            pass

    def __contains__(self, item):
        return item in self._vehicles

    def __iter__(self):
        return iter(self._vehicles)

    def first_vehicle_ahead(self, position):
        deltas = [veh.position - position for veh in self._vehicles]
        try:
            min_pos_delta = min(delta for delta in deltas if delta > 0)
            return self._vehicles[deltas.index(min_pos_delta)]
        except ValueError:
            return None

    def first_vehicle_behind(self, position):
        deltas = [veh.position - position for veh in self._vehicles]
        try:
            min_neg_delta = max(delta for delta in deltas if delta < 0)
            return self._vehicles[deltas.index(min_neg_delta)]
        except ValueError:
            return None

    @staticmethod
    def _almost_eq(a, b, tolerance=1E-9):
        return abs(a - b) < tolerance

    def vehicle_on(self, position):
        return any(Lane._almost_eq(veh.position, position) for veh in self._vehicles)


class World(object):
    _change = namedtuple('_change', ['veh', 'lane', 'speed'])

    def __init__(self, numlanes):
        self._lanes = [Lane(i) for i in range(numlanes)]

        self._lane_change_targets = {}
        self._reset_lane_changes()

    def _reset_lane_changes(self):
        # self._lane_change_targets = tuple([] for _ in range(len(self._lanes)))
        self._lane_change_targets = {}

    def lane(self, num):
        try:
            return self._lanes[num]
        except IndexError:
            return None

    def lanes(self):
        return tuple(self._lanes)

    def left_of(self, lane):
        return self.lane(lane.lane_number - 1)

    def right_of(self, lane):
        return self.lane(lane.lane_number + 1)

    def request_change(self, veh, lane, speed):
        if lane not in self._lane_change_targets:
            self._lane_change_targets[lane] = []
        self._lane_change_targets[lane].append(World._change(veh, lane, speed))

    def _resolve_changes_for_lane(self, lane):
        pairwise_changes = itertools.combinations(self._lane_change_targets[lane], 2)
        for change1, change2 in pairwise_changes:
            veh1, veh2 = change1.veh, change2.veh
            if has_conflict(veh1, veh2):
                # prioritize vehicles that don't change lanes
                # the other vehicle just shouldn't change lanes in that scenario
                if change1.lane is lane:
                    veh1.cruise(speed=change1.speed)
                    veh2.cruise(speed=veh2.max_speed_on())
                elif change2.lane is lane:
                    veh2.cruise(speed=change2.speed)
                    veh1.cruise(speed=veh1.max_speed_on())
                else:
                    # randomly pick to apply change to vehicle 2, leaving vehicle 1 to stay
                    veh1.cruise(veh1.max_speed_on())
                    veh2.change_lane(change2.lane, change2.speed)
            else:
                veh1.change_lane(change1.lane, change1.speed)
                veh2.change_lane(change2.lane, change2.speed)

    def step(self):
        vehs = [veh for lane in self._lanes for veh in lane]

        for veh in vehs:
            veh.calculate()

        for lane in self._lane_change_targets:
            self._resolve_changes_for_lane(lane)

        for veh in vehs:
            veh.apply()

        self._reset_lane_changes()

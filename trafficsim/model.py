# meters
VEHICLE_LENGTH = 4.8


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


class Vehicle(object):
    def __init__(self, position, target_speed, lane, world):
        self.target_speed = target_speed
        self._current_state = VehicleState(position, target_speed, lane)
        self._next_state = VehicleState.undefined()
        lane.add(self)
        self._world = world

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

    def cruise(self):
        self.position = self.next_predicted_position()

    def calculate(self):
        next_lane, next_speed = self._decide_lane_and_speed()
        self._world.register_change(self, next_lane, next_speed)

    def _vehicles_around_position(self, lane):
        return lane.first_vehicle_ahead(self.position), lane.first_vehicle_behind(self.position)

    def _can_change_lane(self, lane):
        if lane is None:
            return False

        if lane is self.lane:
            return True

        lane_veh_ahead, lane_veh_behind = self._vehicles_around_position(lane)
        this_veh_pos = self.next_predicted_position()

        if lane_veh_ahead is None:
            will_hit_vehicle_ahead = False
        else:
            ahead_veh_pos = lane_veh_ahead.next_predicted_position()
            will_hit_vehicle_ahead = abs(ahead_veh_pos - this_veh_pos) < VEHICLE_LENGTH

        if lane_veh_behind is None:
            behind_will_hit_you = False
        else:
            behind_veh_pos = lane_veh_behind.next_predicted_position()
            behind_will_hit_you = abs(behind_veh_pos - this_veh_pos) < VEHICLE_LENGTH

        return not will_hit_vehicle_ahead and not behind_will_hit_you

    def _decide_lane_and_speed(self):
        speed_lanes_map = {}
        for lane in self.lane, self.lane.left, self.lane.right:
            if self._can_change_lane(lane):
                speed_on_lane = self._max_speed_on(lane)
                if speed_on_lane not in speed_lanes_map:
                    speed_lanes_map[speed_on_lane] = []
                speed_lanes_map[speed_on_lane].append(lane)

        max_speed = max(speed_lanes_map)
        # our lane will take priority over left lane will take priority over right lane
        return speed_lanes_map[max_speed][0], max_speed

    def _max_speed_on(self, lane):
        lane_veh_ahead, _ = self._vehicles_around_position(lane)
        if lane_veh_ahead is None:
            return self.target_speed
        else:
            v_threshold = lane_veh_ahead.next_predicted_position() - self.position - VEHICLE_LENGTH
            return min(v_threshold, self.target_speed)

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


class Lane(object):
    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
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


class World(object):
    def __init__(self):
        pass

    def register_change(self, veh, lane, speed):
        pass

    def orchestrate_step(self):
        pass
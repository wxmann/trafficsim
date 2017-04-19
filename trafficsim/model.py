# meters
VEHICLE_LENGTH = 4.8


class VehicleState(object):
    @classmethod
    def undefined(cls):
        return VehicleState(None, None, None, None, None)

    def __init__(self, position, speed, lane, next_vehicle, prev_vehicle):
        self.position = position
        self.speed = speed
        self.lane = lane
        self.next_vehicle = next_vehicle
        self.prev_vehicle = prev_vehicle

    def coalesce(self, another_state):
        self.position = first_not_none(self.position, another_state.position)
        self.speed = first_not_none(self.speed, another_state.speed)
        self.lane = first_not_none(self.lane, another_state.lane)
        self.next_vehicle = first_not_none(self.next_vehicle, another_state.next_vehicle)
        self.prev_vehicle = first_not_none(self.prev_vehicle, another_state.prev_vehicle)


def first_not_none(*args):
    for arg in args:
        if arg is not None:
            return arg
    return None


class Vehicle(object):
    def __init__(self, position, target_speed, lane, next_vehicle=None, prev_vehicle=None):
        self.target_speed = target_speed
        self._current_state = VehicleState(position, target_speed, lane, next_vehicle, prev_vehicle)
        self._next_state = VehicleState.undefined()

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

    @property
    def vehicle_in_front(self):
        return self._current_state.next_vehicle

    @vehicle_in_front.setter
    def vehicle_in_front(self, newveh):
        self._next_state.next_vehicle = newveh

    @property
    def vehicle_behind(self):
        return self._current_state.prev_vehicle

    @vehicle_behind.setter
    def vehicle_behind(self, newveh):
        self._next_state.prev_vehicle = newveh

    # only for testing purposes, not intended for public API consumption
    def set_vehicles(self, veh_front, veh_behind):
        self._current_state.next_vehicle = veh_front
        self._current_state.prev_vehicle = veh_behind

    def next_predicted_position(self):
        return self.position + first_not_none(self._next_state.speed, self.speed)

    def next_ideal_position(self):
        return self.position + self.target_speed

    def calculate(self):
        if self.vehicle_in_front is not None:
            ideal_next_position = self.next_ideal_position()
            front_next_pos = self.vehicle_in_front.next_predicted_position()

            if abs(ideal_next_position - front_next_pos) < VEHICLE_LENGTH:
                if self.lane.left is not None and self.can_change_lane(self.lane.left):
                    self.change_lane(self.lane.left)
                elif self.lane.right is not None and self.can_change_lane(self.lane.right):
                    self.change_lane(self.lane.right)
                else:
                    # brake to match the speed of the guy in front if you can't change lanes
                    self.speed = self.vehicle_in_front.speed
            else:
                # cruise at target speed
                self.speed = self.target_speed
        self.cruise()

    def cruise(self):
        self.position = self.next_predicted_position()

    def _vehicles_around_position(self, lane):
        return lane.first_vehicle_ahead(self.position), lane.first_vehicle_behind(self.position)

    def change_lane(self, newlane):
        newlane_veh_ahead, newlane_veh_behind = self._vehicles_around_position(newlane)
        if newlane_veh_behind is not None:
            newlane_veh_behind.vehicle_in_front = self
        if newlane_veh_ahead is not None:
            newlane_veh_ahead.vehicle_behind = self

        if self.vehicle_in_front is not None:
            self.vehicle_in_front.vehicle_behind = self.vehicle_behind
        if self.vehicle_behind is not None:
            self.vehicle_behind.vehicle_in_front = self.vehicle_in_front

        self.speed = self.target_speed
        self.lane = newlane

    def can_change_lane(self, lane):
        if lane is None:
            return False

        newlane_veh_ahead, newlane_veh_behind = self._vehicles_around_position(lane)
        this_veh_pos = self.next_ideal_position()

        if newlane_veh_ahead is None:
            will_hit_vehicle_ahead = False
        else:
            ahead_veh_pos = newlane_veh_ahead.next_predicted_position()
            will_hit_vehicle_ahead = abs(ahead_veh_pos - this_veh_pos) < VEHICLE_LENGTH

        if newlane_veh_behind is None:
            behind_will_hit_you = False
        else:
            behind_veh_pos = newlane_veh_behind.next_predicted_position()
            behind_will_hit_you = abs(behind_veh_pos - this_veh_pos) < VEHICLE_LENGTH

        return not will_hit_vehicle_ahead and not behind_will_hit_you

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

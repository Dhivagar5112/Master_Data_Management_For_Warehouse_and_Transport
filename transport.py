class Vehicle:
    def __init__(self, vehicle_id, driver_name, capacity):
        self.vehicle_id = vehicle_id
        self.driver_name = driver_name
        self.capacity = capacity
        self.available = True

    def assign(self):
        if self.available:
            self.available = False
            return f"Vehicle {self.vehicle_id} assigned."
        return f"Vehicle {self.vehicle_id} is not available."

    def release(self):
        self.available = True
        return f"Vehicle {self.vehicle_id} is now available."


class TransportManager:
    def __init__(self):
        self.vehicles = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def show_vehicles(self):
        for v in self.vehicles:
            status = "Available" if v.available else "Busy"
            print(f"ID: {v.vehicle_id}, Driver: {v.driver_name}, Status: {status}")

    def assign_vehicle(self):
        for v in self.vehicles:
            if v.available:
                print(v.assign())
                return
        print("No vehicles available.")


# Example usage
if __name__ == "__main__":
    tm = TransportManager()

    v1 = Vehicle("V001", "Ravi", 1000)
    v2 = Vehicle("V002", "Kumar", 1500)

    tm.add_vehicle(v1)
    tm.add_vehicle(v2)

    tm.show_vehicles()
    tm.assign_vehicle()
    tm.show_vehicles()
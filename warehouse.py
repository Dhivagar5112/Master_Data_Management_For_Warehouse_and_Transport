class Product:
    def __init__(self, product_id, name, quantity):
        self.product_id = product_id
        self.name = name
        self.quantity = quantity

    def add_stock(self, amount):
        self.quantity += amount

    def remove_stock(self, amount):
        if amount > self.quantity:
            return "Not enough stock!"
        self.quantity -= amount
        return "Stock updated."


class Warehouse:
    def __init__(self):
        self.inventory = {}

    def add_product(self, product):
        self.inventory[product.product_id] = product

    def show_inventory(self):
        print("\nInventory:")
        for p in self.inventory.values():
            print(f"{p.product_id} - {p.name}: {p.quantity}")

    def update_stock(self, product_id, amount, add=True):
        if product_id in self.inventory:
            if add:
                self.inventory[product_id].add_stock(amount)
            else:
                print(self.inventory[product_id].remove_stock(amount))
        else:
            print("Product not found!")


# Example usage
if __name__ == "__main__":
    wh = Warehouse()

    p1 = Product("P001", "Laptop", 10)
    p2 = Product("P002", "Mouse", 50)

    wh.add_product(p1)
    wh.add_product(p2)

    wh.show_inventory()

    wh.update_stock("P001", 5, add=True)
    wh.update_stock("P002", 10, add=False)

    wh.show_inventory()


class Person:

    def __init__(self, id: int, firstname: str, lastname: str, email: str, city: str) -> None:
        self.id: int = id
        self.firstname: str = firstname
        self.lastname: str = lastname
        self.city: str = city
        self.email: str = email
        self.owner_id: int | None = None

    @property
    def fullname(self):
        return f'{self.firstname} {self.lastname}'
    
    def allocate(self, owner_id: int):
        if self.owner_id is not None:
            raise ValueError('Person\'s data already have an owner!')
        self.owner_id = owner_id

    def reallocate(self, owner_id: int):
        self.owner_id = owner_id
    
    def release(self):
        self.owner_id = None
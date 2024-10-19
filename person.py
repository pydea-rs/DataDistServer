from typing import Dict

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
        if not self.is_free:
            raise ValueError('Person\'s data already have an owner!')
        self.owner_id = owner_id

    def reallocate(self, owner_id: int):
        self.owner_id = owner_id
    
    def release(self):
        self.owner_id = None
        
    @property
    def is_free(self):
        return self.owner_id is None
    
    def is_owned_by(self, client_id: int):
        return not self.is_free and client_id == self.owner_id
 
    def to_dict(self) -> Dict[str, str | int | float]:
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "city": self.city,
        }
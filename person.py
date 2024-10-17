

class Person:

    def __init__(self, id: int, firstname: str, lastname: str, email: str, location: str) -> None:
        self.id: int = id
        self.firstname: str = firstname
        self.lastname: str = lastname
        self.location: str = location
        self.email: str = email

    @property
    def fullname(self):
        return f'{self.firstname} {self.lastname}'
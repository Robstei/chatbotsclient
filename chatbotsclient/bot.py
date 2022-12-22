import json


class Bot:
    """Bot"""

    def __init__(
        self,
        id: str,
        name: str,
        method: str = None,
    ):
        self.__id = id
        self.__name = name
        self.__method = method

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    @property
    def method(self):
        return self.__method

    def to_json(self) -> str:
        return json.dumps(
            {
                "id": self.id,
                "name": self.name,
                "method": self.method,
            }
        )

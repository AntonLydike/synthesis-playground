from abc import ABC, abstractmethod


class Ordered(ABC):
    """
    Implementes order on any object that can provide a "key" to be ordered by.
    """

    @abstractmethod
    def key(self):
        raise NotImplementedError()

    def __lt__(self, other):
        if isinstance(other, Ordered):
            return self.key() < other.key()
        raise NotImplementedError()

    def __gt__(self, other):
        if isinstance(other, Ordered):
            return self.key() > other.key()
        raise NotImplementedError()

    def __le__(self, other):
        if isinstance(other, Ordered):
            return self.key() <= other.key()
        raise NotImplementedError()

    def __ge__(self, other):
        if isinstance(other, Ordered):
            return self.key() >= other.key()
        raise NotImplementedError()

    def __eq__(self, other):
        return isinstance(other, Ordered) and self.key() == other.key()


class DataclassOrder(Ordered):
    def key(self):
        return tuple(
            getattr(self, attr) for attr in self.__dataclass_fields__
        )

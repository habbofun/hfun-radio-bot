def Singleton(cls):
    """
    Decorator function that transforms a class into a singleton.

    Args:
        cls: The class to be transformed into a singleton.

    Returns:
        The singleton instance of the class.

    Example:
        @Singleton
        class MyClass:
            pass

        obj1 = MyClass()  # Creates a new instance
        obj2 = MyClass()  # Returns the same instance as obj1
        assert obj1 is obj2  # True
    """
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance

class classname(superclass):
    """Class docstring."""
    def method(self, *args, **kwargs):
        """Method docstring."""
        pass
    """Another class docstring."""
    @decorator
    @decorator2(1, 2, 3)
    def method2(self, *args, **kwargs):
        """Method2 docstring."""
        pass
    """Yet another class docstring."""
    @decorator
    class subclass:
        """Subclass docstring."""
        @decorator
        @decorator2()
        def method3(self, *args, **kwargs):
            """Method3 docstring."""
            pass

import abc


class Shape(abc.ABC):

    @abc.abstractmethod
    def my_method(self, input):
        """
        Me stuff
        """
        pass


class Rectangle(Shape):

    def my_method(self, input1, input2):
        print("my concrete method")
        return 0


def main():
    
    #my_shape = Shape()
    #my_shape.my_method(0)
    my_rectangle = Rectangle()
    my_rectangle.my_method(0,1)

main()
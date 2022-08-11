# "x": "34 29.514",
# "y": "-118 16.980",

def wrapper(input_int):
    def dm(x):
        degrees = int(x) // 100
        minutes = x - 100*degrees
        return degrees, minutes

    def decimal_degrees(degrees, minutes):
        return degrees + minutes/60 

    return decimal_degrees(*dm(input_int))

print (wrapper(3429.514))
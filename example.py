
import uml

old_obj = {"some data": ["some other data", 1, 2, 3, None]}

serialized = uml.serialize(old_obj)
print(repr(serialized))

obj = uml.parse(serialized)

assert obj == old_obj


from z9c import pack, unpack, PacketStatus
from pandas import DataFrame
import numpy as np
gb = 41666666
x = DataFrame([np.random.random() for _ in range(gb)])
import sys
print(f"Size of file is {sys.getsizeof(x) * 10 ** -6} Mb")
input("hit any key to cont.")
import timeit
start = timeit.default_timer()
assert bytes(x) == bytes(unpack(pack(x, "ACK"))[0]) #check algorithm
print("="*42 + f"\nPassed pack/unpack check in {round(timeit.default_timer() - start, 3)} Seconds!")
from uuid import uuid4
print(pack(str(uuid4()), "ACK"))
from z9c import pack, unpack, PacketStatus
from pandas import DataFrame
x = DataFrame()
input("hit any key to cont.")
import timeit
start = timeit.default_timer()
assert bytes(x) == bytes(unpack(pack(x, "ACK"))[0]) #check algorithm
print("="*42 + f"\nPassed pack/unpack check in {round(timeit.default_timer() - start, 3)} Seconds!")

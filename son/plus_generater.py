mod=87
with open("example.txt", "w", encoding="utf-8") as f:
    for i in range(mod):
        for j in range(mod):
            print(f"{i} + {j} = {(i+j)%mod}",file=f)
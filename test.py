with open('manual-tmp.txt', 'r') as f:     
    lines = f.readlines()
    print(len(lines))
   
for l in lines:
    if '  -  ' in l:
        print(l, end="")

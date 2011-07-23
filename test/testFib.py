a={0:0,1:1,2:1,3:2}
def b(c):
 if c not in a:d=c//2;e=c%2;f=e*2-1;a[c]=b(d+1)**2+f*b(d+e-1)**2
 return a[c]

b={0:0,1:1,2:1,3:2}
def c(a):
 if a not in b:d=a//2;e=a%2;f=e*2-1;b[a]=c(d+1)**2+f*c(d+e-1)**2
 return b[a]

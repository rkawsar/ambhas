Wiki for using the copula library

# Initialize the class #

```
x = np.random.normal(size=100)
y = np.random.normal(size=100)
foo = Copula(x, y, 'frank')
u,v = foo.generate(100)
```

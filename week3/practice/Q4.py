import matplotlib.pyplot as plt
x=[1,2,3,4,5]
y=[2,4,6,8,10]
plt.plot(x,y,marker='o',color='g',linestyle='--',label='y=2x')
plt.xlabel("X-axis")
plt.ylabel("y-axis")
plt.title("Line Graph")
plt.legend()
plt.show()

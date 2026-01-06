import debugpy
count =1

def wth(count):
       while count >0:
         debugpy.breakpoint() 
         print("Count is:", count)
         count -=1
wth(3)  
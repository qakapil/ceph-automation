'''
Created on Jul 11, 2014

@author: kapil
'''


def launch(*wargs):
    print str(wargs)
    print type(wargs)
    print (wargs[0][0])

if __name__ == '__main__':
    l = [1,2,3,4]
    launch(l)
    pass
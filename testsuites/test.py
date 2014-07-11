'''
Created on Jul 11, 2014

@author: kapil
'''


def launch(dict):
    print(dict['name'])
    print(dict['age'])
    a = dict.get('pool','rbd')
    print a

if __name__ == '__main__':
    d = {'name':1, 'age':3}
    launch(d)
    pass
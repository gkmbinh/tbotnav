#!/usr/bin/python

from Tkinter import *
import os

root = Tk(className = 'face_recognition_gui')
svalue = StringVar() # defines the widget state as string

w = Entry(root,textvariable=svalue) # adds a textarea widget
w.pack()

def train_fisher_btn_load():
    name = svalue.get()
    os.system('rosrun tbotnav train_faces.py %s'%name)

def train_eigen_btn_load():
    name = svalue.get()
    os.system('rosrun tbotnav train_faces2.py %s'%name)

def recog_fisher_btn_load():
    os.system('rosrun tbotnav face_recog.py')

def recog_eigen_btn_load():
    os.system('rosrun tbotnav face_recog2.py')
    
train_btn = Button(root,text="Train (Fisher)", command=train_fisher_btn_load)
train_btn.pack()

recog_btn = Button(root,text="Recognize (Fisher)", command=recog_fisher_btn_load)
recog_btn.pack()

train_btn = Button(root,text="Train (Eigen)", command=train_eigen_btn_load)
train_btn.pack()

recog_btn = Button(root,text="Recognize (Eigen)", command=recog_eigen_btn_load)
recog_btn.pack()

root.mainloop()
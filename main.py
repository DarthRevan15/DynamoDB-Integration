from flask import Flask, render_template, request, redirect, url_for
from flaskext.markdown import Markdown
import pickle
from os import path as os_path, mkdir as os_mkdir, remove as os_remove
from datetime import datetime
import sys, getopt

import boto3
from botocore.config import Config
import pprint

app = Flask("Champagne")
Markdown(app)
   
dynamodb = boto3.client("dynamodb", config = Config(region_name = "us-east-1"))
pp = pprint.PrettyPrinter(indent=4)




@app.route("/")
def home():
    response = dynamodb.scan(TableName = "Notes")
    response = response["Items"]
    if response is not None:
        pp.pprint(response)
    else:
        pass
    return render_template("home.html", notes=noteList)

@app.route("/addNote")
def addNote():
    return render_template("noteForm.html", headerLabel="New Note", submitAction="createNote", cancelUrl=url_for('home'))

@app.route("/createNote", methods=["post"])
def createNote():
    # get next note id
    response = dynamodb.scan(TableName = "Notes")
    if len(noteList):
        idList = [ int(i['ID']["N"]) for i in response ]
        noteId = str(max(idList)+1)
    else:
        noteId = "1"


    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']

    dynamodb.put_item(TableName = "Notes", Item = {"ID":{"N":noteId}, "Title":{"S":noteTitle}, "lastModified":{"S":lastModifiedDate},
        "Message":{"S":noteMessage}})

    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/viewNote/<int:noteId>")
def viewNote(noteId):
    noteId = str(noteId)

    response = dynamodb.scan(TableName = "Notes")
    note = dynamodb.get_item(TableName = "Notes", Key ={"ID":{"N":noteId}})
    pp.pprint(note)
    
    note = note["Item"]
    pp.pprint(note)
    
    return render_template("viewNote.html", note=note, submitAction="/saveNote")

@app.route("/editNote/<int:noteId>")
def editNote(noteId):
    noteId = str(noteId)

    response = dynamodb.scan(TableName = "Notes")
    note = dynamodb.get_item(TableName = "Notes", Key ={"ID":{"N":noteId}})
    note = note["Item"]
    
    cancelUrl = url_for('viewNote', noteId=noteId)
    return render_template("noteForm.html", headerLabel="Edit Note", note=note, submitAction="/saveNote", cancelUrl=cancelUrl)

@app.route("/saveNote", methods=["post"])
def saveNote():
    lastModifiedDate = datetime.now()
    lastModifiedDate = lastModifiedDate.strftime("%d-%b-%Y %H:%M:%S")

    noteId = str(int(request.form['noteId']))
    noteTitle = request.form['noteTitle']
    noteMessage = request.form['noteMessage']
    
    response = dynamodb.scan(TableName = "Notes")
    dynamodb.put_item(TableName = "Notes", Item ={"ID":{"N":noteId}, "Title":{"S":noteTitle}, "lastModified":{"S":lastModifiedDate},
        "Message":{"S":noteMessage}}) 

    return redirect(url_for('viewNote', noteId=noteId))

@app.route("/deleteNote/<int:noteId>")
def deleteNote(noteId):

    response = dynamodb.scan(TableName = "Notes")
    # remove the note from the list of note metadata
    global noteList
    newNoteList = [ i for i in response if not (i['ID'] == noteId) ]
    noteList = newNoteList
    
    dynamodb.delete_item(TableName = "Notes", Item ={"ID":{"N":noteId}, "Title":{"S":noteTitle}, "lastModified":{"S":lastModifiedDate},
        "Message":{"S":noteMessage}})

    return redirect("/")

if __name__ == "__main__":
    debug = False

    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:p:", ["debug"])
    except getopt.GetoptError:
        print('usage: main.py [-h 0.0.0.0] [-p 5000] [--debug]')
        sys.exit(2)

    port = "5000"
    host = "0.0.0.0"
    print(opts)
    for opt, arg in opts:
        if opt == '-p':
            port = arg
        elif opt == '-h':
            host = arg
        elif opt == "--debug":
            debug = True

    app.run(host=host, port=port, debug=debug)


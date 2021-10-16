import pymongo
import ssl

from pymongo.write_concern import WriteConcern

uri = "mongodb+srv://bot-bukbuk:nielquktRanehMr2@cluster0.dik8l.mongodb.net/myFirstDatabase?retryWrites=true&w=majority"


try:
    client = pymongo.MongoClient(uri, ssl_cert_reqs=ssl.CERT_NONE)
    client.server_info()  # force connection on a request as the
    # connect=True parameter of MongoClient seems
    mydb = client["bukbuk"]
    print("Connected")
except Exception as err:
    # do whatever you need
    print(f'err : {err} connection failed ..')


def wrapperResult(document, args, msg):
    return {"data": document, "err": args, "messages": msg}


def insertOne(document, collection):
    try:
        mycol = mydb[collection]
        insertOne = mycol.insert_one(document)
        return wrapperResult(document, False, "success")
    except Exception as err:
        print(f'err : {err} failed insert data ..')
        return wrapperResult(None, True, err)

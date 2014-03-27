#!/usr/bin/env python3
import csv, os, itertools, binascii, pprint
from collections import defaultdict

def hexlify(a):
	return binascii.hexlify(a.encode("utf-8")).decode("utf-8")

def blockid(i):
	return i["BlockNumber"] + "_" + hexlify(i["BlockTime"])

def getdata():
	with open("bitcoin.csv", "r", newline="") as f:
		def lines():
			seen = False
			for i in f:
				if i.startswith("### Block"):
					if seen:
						continue
					else:
						i = i[4:]
						seen = True
				if i.startswith("\"####"): continue
				if len(i.strip()) == 0: continue
				yield i
		yield from csv.DictReader(lines())

def highest_set(fmt, iterable):
	for i in itertools.count():
		if fmt.format(i) not in iterable:
			return i

def blocks():
	d = defaultdict(lambda: {"OutputValue": 0, "FeesValue": 0, "NumTransactions": 0, "Size": 112 + 1}) # 112 is the block header size, 1 is nTx count
	for i in getdata():
		output_value, input_value, fees_value = values(i)
		k = blockid(i)
		d[k]["OutputValue"] += output_value
		d[k]["FeesValue"] += fees_value
		d[k]["NumTransactions"] += 1
		d[k]["Size"] += int(i["TransactionSize"])
		d[k].update({
			"ID": k,
			"Hash": None,
			"Version": None,
			"Timestamp": i["BlockTime"],
			"Nonce": None,
			"Difficulty": None,
			"Merkle": None,
		})
	yield from d.values()

def values(i):
	output_value = sum(float(i["Output{}Value".format(idx)]) for idx in range(1, int(i["OutputCount"])+1))
	input_value = sum(float(i["Input{}Amount".format(idx)]) if float(i["Input{}Amount".format(idx)]) != 0 else 50 for idx in range(1, int(i["InputCount"])+1))
	fees_value = abs(input_value - output_value) % 25
	return output_value, input_value, fees_value

def transactions():
	for idx, i in enumerate(getdata()):
		output_value, input_value, fees_value = values(i)
		if fees_value > 0.001: pprint.pprint(fees_value)
		yield {
			"ID": i["TransactionHash"],
			"Hash": i["TransactionHash"], 
			"Version": i["TransactionVersionNumber"],
			"BlockId": blockid(i),
			"NumInputs": i["InputCount"], #highest_set("Input{}Hash", i),
			"NumOutputs": i["OutputCount"], #highest_set("Output{}Hash", i),
			"OutputValue": output_value,
			"FeesValue": fees_value,
			"LockTime": None,
			"Size" : i["TransactionSize"], 
		}

def outputs():
	for i in getdata():
		for idx in range(1, int(i["OutputCount"])+1):
			yield {
				"TransactionId": i["TransactionHash"],
				"Index": idx,
				"Value": i["Output{}Value".format(idx)],
				"Script": i["Output{}Script".format(idx)],
				"ReceivingAddress": i["Output{}Key".format(idx)],
				"InputTxHash": None,  # also NULL in blockparser:
				"InputTxIndex": None, # https://github.com/mcdee/blockparser/blob/master/cb/csv.cpp#L308
			}

def inputs():
	for i in getdata():
		for idx in range(1, int(i["InputCount"])+1):
			yield {
				"TransactionId": i["TransactionHash"],
				"Index": idx,
				"Script": i["Input{}Script".format(idx)],
				"OutputTxHash": None,
				"OutputTxIndex": None,
			}

def write(filename, fields, iterable):
	with open(filename, "a", newline="") as f:
		w = csv.DictWriter(f, fields)
		if os.fstat(f.fileno()).st_size == 0:
			w.writeheader()
		w.writerows(iterable)

write("blocks.csv", ["ID","Hash","Version","Timestamp","Nonce","Difficulty","Merkle","NumTransactions","OutputValue","FeesValue","Size"], blocks())
write("transactions.csv", ["ID","Hash","Version","BlockId","NumInputs","NumOutputs","OutputValue","FeesValue","LockTime","Size"], transactions())
write("outputs.csv", ["TransactionId","Index","Value","Script","ReceivingAddress","InputTxHash","InputTxIndex"], outputs())
write("inputs.csv", ["TransactionId","Index","Script","OutputTxHash","OutputTxIndex"], inputs())

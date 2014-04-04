#!/home/ubuntu/sdb/block/bin/python3
import sys,json,itertools,collections
resp = json.loads(sys.stdin.read())['response']
l = (((i, (x['points'], x['message'])) for i in x["thread"]['identifiers']) for x in resp)
l = itertools.chain.from_iterable(l)
a = collections.defaultdict(lambda: (-1,""))
a.update((x[0], x[1]) for x in l if x[1][0] > a[x[0]][0])
print(json.dumps(dict((x, y[1]) for x,y in a.items())))

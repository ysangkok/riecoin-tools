#!/home/ubuntu/sdb/block/bin/python3
import pexpect

with open("logfile.txt","wb") as f:
 p = pexpect.spawn("nice ../blockchain.out /home/ubuntu/sdb/riecoindata/blocks", timeout=3000, logfile=f)
 p.expect("exit, quit, or bye    : Will exit this tool")
 p.sendline("statistics")
 p.expect("\\*\\*\\* WARNING : This will consume an enormous amount of memory! \\*\\*\\*")
 p.sendline("analyze")
 p.expect("Transaction Input Signature Analysis set to: true")
 #p.sendline("export")
 #p.expect("Export Transactions set to: true")
 p.sendline("record_addresses")
 p.expect("record_addresses set to true")
 p.sendline("scan")
 p.expect("To gather statistics so you can ouput balances of individual addresses, you must execute the 'statistics' command prior to running the process command.")
 p.sendline("process")
 p.expect("Saving statistics to file 'stats.csv")
 p.sendline("top_balance 1000")
 p.sendline("zombie 30")
 p.sendline("dump")
 p.sendline("bye")
 p.expect(pexpect.EOF)

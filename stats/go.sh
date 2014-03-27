#!/usr/bin/env bash
SCRIPT_PATH="${BASH_SOURCE[0]}";
cd `dirname ${SCRIPT_PATH}`

cd out
rm *
../stats.py

BEGIN=$(grep -nm 1 "Days,Value,FirstUsed,LastReceived,LastSpent,TotalSent,TotalReceived,TransactionCount,PublicKeyAddress" < stats.csv | cut -d: -f1)
END=$(grep -nm 1 "Summary statistics for 1 months." < stats.csv | cut -d: -f1)
sed -n $BEGIN,$(expr $END - 1)p < stats.csv > days_value.csv
A='python3 -c "import sys,csv; csv.writer(sys.stdout).writerows(zip(*csv.reader(sys.stdin)))"'
grep -A 3 "^Summary statistics for 1 months." < stats.csv | tail -n2 | eval $A > summary.csv # table
grep -A 3 "^Bitcoin Public Key Address Distribution Count by balance." < stats.csv | tail -n2 | eval $A > address_balance_threshold_count.csv # pie chart
sed -i '1s/.*/threshold,count/' address_balance_threshold_count.csv
sed -i '2d' address_balance_threshold_count.csv
grep -A 3 "^Bitcoin Public Key Address Distribution Total Value by balance." < stats.csv | tail -n2 | eval $A > average_assets_by_balance.csv # pie chart
sed -i '1s/.*/threshold,count/' average_assets_by_balance.csv
grep -A 11 "^Bitcoin value distribution based on age." < stats.csv | tail -n +2 > total_assets_and_address_count_by_age.csv # bar chart
tail -n +9 < DumpByBalance.csv > short.csv
sqlite3 db < ../balances.sql

rm ~/sdb/www/stat_results/*
cp -l * ~/sdb/www/stat_results/

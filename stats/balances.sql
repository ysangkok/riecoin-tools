create table balances (address text primary key, balance real, dayslastsent integer);
.separator ","
.import short.csv balances

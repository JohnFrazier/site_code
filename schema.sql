
drop table if exists Page;
create table Page (
  id integer primary key autoincrement,
  page_name string not null,
  ctime timestamp not null,
  content text not null
);

drop table if exists User;
create table User (
  id integer primary key autoincrement,
  username string not null,
  ctime timestamp not null,
  password string not null 
);

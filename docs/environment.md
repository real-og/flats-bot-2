# Environment

## Software preparation

First make sure you have installed Postgresql and redis on your machine. Both services should work.
Then let's create postgres database and a table in it.

After ```psql``` command normally we are under `postgres` user.

To create database ```CREATE DATABASE flats_bot;```

To connect to it ```\c flats_bot```

here we are creating a table
```
CREATE TABLE IF NOT EXISTS users (
            id serial PRIMARY KEY,
            id_tg bigint not null,
            username varchar(51) default NULL,
            isactive boolean default false,
            jointime timestamp without time zone default CURRENT_TIMESTAMP(1),
            params json default '{"minCost": 0,
                "maxCost": 10000,
                "town": "",
                "landlord": "",
                "rooms": [],
                "isSubwayNeed": false,
                "subways": [],
                "subway_dist": 10000,
                "isPointNeed": false,
                "lat": "",
                "lon": "",
                "point_dist" : 10000,
                "source": []}'
            );
```

To get back `\q`

Then we create user for the app `createuser -P flatsdbuser`
After that we can connect to `flats-bot` db under `postgres` user and grant all privileges

```
grant all on users_id_seq to flatsdbuser;
grant all on users to flats_admin;
```

## env variables

You have to create `.env` file in the root of directory near the .env.example and fill it with your data:

- BOT_TOKEN - token you get from BotFather in telegram
- ADMIN_ID - id of account you want be with rights to get users stats, error logs and broadcast via bot
- database, user, password, host, port - your postgres credits
- ROOT_PATH - the path to the root of directory on your machine. If you use linux or Mac, just type `pwd` in the terminal in the root directory and put the output to .env

## running

I usually use pipenv for working with virtual envs in python but this is not necessary. 
To install pipenv
```
pip install pipenv
```

To create environment
```
pipenv shell
```

To install all we need (you may do it manually)
```
pipenv install -r requirements.txt
```

To run bot and service
```
python src/service/main_flats_parser.py
python src/bot/main_flats_bot.py
```









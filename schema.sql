-- psql
-- postgres=#
CREATE DATABASE flats_bot;

-- \c flats_bot #connect to db

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

-- \q

-- createuser -P flatsdbuser

-- then in flats_bot db under the user of postgres grant access
-- grant all on users_id_seq to flatsdbuser;
-- grant all on users to flats_admin;
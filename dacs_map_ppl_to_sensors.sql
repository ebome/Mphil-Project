/*
SELECT * FROM dacs_db.sensors where sensor_type = 'Sleep';

Create table dacs_db.joined_gateway
(SELECT
dacs_db.gateways.gateway_id, dacs_db.gateways.home_id, dacs_db.homes.PID, dacs_db.rooms.room_id
from dacs_db.gateways 
inner join dacs_db.homes on dacs_db.gateways.home_id = dacs_db.homes.home_id
inner join dacs_db.rooms on dacs_db.gateways.gateway_id = dacs_db.rooms.gateway_id
where dacs_db.homes.PID like "%3%" );

create table dacs_db.joined_sleep_sensor(
SELECT
dacs_db.joined_gateway.room_id, dacs_db.sensors.sensor_id, dacs_db.sensors.sensor_name, 
dacs_db.sensors.sensor_type, dacs_db.sensors.sensor_udn
from dacs_db.joined_gateway 
inner join dacs_db.sensors on dacs_db.joined_gateway.room_id = dacs_db.sensors.room_id
where dacs_db.sensors.sensor_type = 'Sleep')


create table dacs_db.All_98_DACS_paticipants
(select dacs_db.emfit_summary_data.*
from dacs_db.joined_sleep_sensor 
inner join dacs_db.emfit_summary_data
on dacs_db.joined_sleep_sensor.sensor_udn = dacs_db.emfit_summary_data.sensor_udn)

*/
-- SELECT sensor_id, count(*) c FROM dacs_db_up_to_may.joined_sleep_sensor group by sensor_id having c>1

select
dacs_db.joined_sleep_sensor.sensor_udn, dacs_db.emfit_summary_data.*
from dacs_db.joined_sleep_sensor 
inner join dacs_db.emfit_summary_data
on dacs_db.joined_sleep_sensor.sensor_udn = dacs_db.emfit_summary_data.sensor_udn







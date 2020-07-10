# Get Motion sensor data
create table dacs_db_up_to_may.joined_motion_sensor_id(
SELECT
dacs_db_up_to_may.joined_gateway.room_id, dacs_db.sensors.sensor_id, dacs_db.sensors.sensor_name, 
dacs_db.sensors.sensor_type, dacs_db.sensors.sensor_udn
from dacs_db_up_to_may.joined_gateway 
inner join dacs_db.sensors on dacs_db_up_to_may.joined_gateway.room_id = dacs_db.sensors.room_id
where dacs_db.sensors.sensor_type = 'Motion');

create table dacs_db_up_to_may.joined_motion_sensor_with_pid(
SELECT
dacs_db_up_to_may.joined_gateway.PID, dacs_db.joined_motion_sensor_id.*
from dacs_db_up_to_may.joined_motion_sensor_id 
inner join dacs_db.joined_gateway on dacs_db_up_to_may.joined_gateway.room_id = dacs_db.joined_motion_sensor_id.room_id);

# Add PID to All_DACS_paticipants_motion
create table dacs_db_up_to_may.All_DACS_paticipants_motion
(select dacs_db_up_to_may.joined_motion_sensor_with_pid.*, dacs_db_up_to_may.sensor_data.timestamp,dacs_db_up_to_may.sensor_data.local_timestamp,dacs_db_up_to_may.sensor_data.sensor_value
from dacs_db_up_to_may.joined_motion_sensor_with_pid 
inner join dacs_db_up_to_may.sensor_data
on dacs_db_up_to_may.joined_motion_sensor_with_pid.sensor_id = dacs_db_up_to_may.sensor_data.sensor_id);


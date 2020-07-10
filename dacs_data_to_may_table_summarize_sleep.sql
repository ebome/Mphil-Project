create table dacs_db_up_to_may.DACS_device_id_mapped
(select dacs_db_up_to_may.joined_sleep_sensor.PID, dacs_db_up_to_may.emfit_summary_data.* 
from dacs_db_up_to_may.joined_sleep_sensor 
inner join dacs_db_up_to_may.emfit_summary_data
on dacs_db_up_to_may.joined_sleep_sensor.sensor_id = dacs_db_up_to_may.emfit_summary_data.device_id);

# Add columns to convert uni timestamp into datetime
ALTER table dacs_db_up_to_may.dacs_device_id_mapped ADD COLUMN start_date varchar(28) AFTER device_id; 
-- ALTER table dacs_db_up_to_may.dacs_device_id_mapped drop column start_date
update dacs_db_up_to_may.dacs_device_id_mapped set start_date=from_unixtime(start_time);

ALTER table dacs_db_up_to_may.dacs_device_id_mapped ADD COLUMN end_date varchar(28) AFTER start_date; 
-- ALTER table dacs_db_up_to_may.dacs_device_id_mapped drop column end_date
update dacs_db_up_to_may.dacs_device_id_mapped set end_date=from_unixtime(end_time);

update dacs_db_up_to_may.dacs_device_id_mapped set start_date=date_format(start_date, '%Y-%m-%d %H:%m:%s'); 
update dacs_db_up_to_may.dacs_device_id_mapped set end_date=date_format(end_date, '%Y-%m-%d %H:%m:%s'); 
